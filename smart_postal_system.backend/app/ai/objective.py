"""
OR-Tools CP-SAT Objective Builder
==================================

Constructs the CP-SAT objective function for the postal route
optimization model.

Objective (Maximise, integer-scaled)
-------------------------------------
  + vehicle_capacity_headroom  × w_vehicle_capacity
  + employee_workload_headroom × w_employee_workload
  + priority_score             × w_parcel_priority
  − distance_cost              × w_distance
  − duration_cost              × w_duration

All float values are multiplied by ``SCALE`` (default 1000) before
being fed into OR-Tools, which operates in integer space only.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, TYPE_CHECKING

from app.ai.ai_utils import (
    SCALE,
    PRIORITY_SCORE,
    compute_avg_priority_score,
    compute_total_weight,
    get_parcel_priority,
    get_vehicle_capacity,
    get_route_distance,
    get_route_duration,
)

if TYPE_CHECKING:
    from ortools.sat.python.cp_model import CpModel
    from app.ai.variable import VariableSet

logger = logging.getLogger(__name__)


class PrecomputedScores:
    """
    Pre-computed integer-scaled scores for each vehicle and employee.

    These are computed once and fed into the objective so the solver
    can work entirely in integer space.
    """

    def __init__(
        self,
        *,
        vehicle_scores: List[int],
        employee_scores: List[int],
        priority_score_scaled: int,
        dist_cost_scaled: int,
        dur_cost_scaled: int,
        avg_priority_raw: float,
    ):
        self.vehicle_scores = vehicle_scores
        self.employee_scores = employee_scores
        self.priority_score_scaled = priority_score_scaled
        self.dist_cost_scaled = dist_cost_scaled
        self.dur_cost_scaled = dur_cost_scaled
        self.avg_priority_raw = avg_priority_raw

    @classmethod
    def from_inputs(
        cls,
        *,
        vehicles: List[Any],
        employees: List[Any],
        parcels: List[Any],
        route: Any,
    ) -> "PrecomputedScores":
        """
        Derive all integer-scaled scores from the raw ORM objects.
        """
        total_weight = compute_total_weight(parcels)
        n_parcels = len(parcels)
        distance_km = get_route_distance(route)
        duration_min = get_route_duration(route)

        # Vehicle capacity headroom (0..SCALE)
        vehicle_scores: List[int] = []
        for veh in vehicles:
            cap = get_vehicle_capacity(veh)
            headroom = max(0.0, (cap - total_weight) / cap) if cap > 0 else 0.0
            vehicle_scores.append(int(headroom * SCALE))

        # Employee workload headroom (may be negative → clamped at objective)
        employee_scores: List[int] = []
        for emp in employees:
            cur = getattr(emp, "current_workload", 0)
            mx = max(getattr(emp, "max_workload", 1), 1)
            headroom = max(0.0, (mx - cur - n_parcels) / mx)
            employee_scores.append(int(headroom * SCALE))

        # Average priority (scaled)
        avg_priority_raw = compute_avg_priority_score(parcels)
        priority_score_scaled = int(avg_priority_raw * SCALE)

        # Distance / duration cost (lower = better → negated in objective)
        dist_cost_scaled = int(min(distance_km, 10_000) * SCALE / 100)
        dur_cost_scaled = int(min(duration_min, 10_000) * SCALE / 1_200)

        return cls(
            vehicle_scores=vehicle_scores,
            employee_scores=employee_scores,
            priority_score_scaled=priority_score_scaled,
            dist_cost_scaled=dist_cost_scaled,
            dur_cost_scaled=dur_cost_scaled,
            avg_priority_raw=avg_priority_raw,
        )


class ScaledWeights:
    """
    Integer-scaled optimisation weights derived from the request payload.
    """

    def __init__(self, weights: Dict[str, float]):
        self.vehicle_capacity = max(int(weights.get("vehicle_capacity", 15) * SCALE), 1)
        self.employee_workload = max(int(weights.get("employee_workload", 20) * SCALE), 1)
        self.parcel_priority = max(int(weights.get("parcel_priority", 20) * SCALE), 1)
        self.distance = max(int(weights.get("distance", 25) * SCALE), 1)
        self.duration = max(int(weights.get("duration", 20) * SCALE), 1)


class ORToolsObjectiveBuilder:
    """
    Constructs the CP-SAT maximisation objective on a given model.
    """

    @staticmethod
    def build(
        model: "CpModel",
        variables: "VariableSet",
        scores: PrecomputedScores,
        weights: Dict[str, float],
    ) -> ScaledWeights:
        """
        Add the objective function to *model*.

        Returns the ``ScaledWeights`` instance (useful for post-solve
        normalisation of the objective value).
        """
        from ortools.sat.python import cp_model as cp

        sw = ScaledWeights(weights)

        # Vehicle capacity headroom contribution
        veh_obj = model.new_int_var(0, SCALE, "veh_obj")
        model.add(
            veh_obj == cp.LinearExpr.weighted_sum(
                variables.vehicle_selected,
                scores.vehicle_scores,
            )
        )

        # Employee workload headroom contribution
        emp_obj = model.new_int_var(-SCALE, SCALE, "emp_obj")
        model.add(
            emp_obj == cp.LinearExpr.weighted_sum(
                variables.employee_selected,
                scores.employee_scores,
            )
        )

        # Maximise weighted combination
        model.maximize(
            sw.vehicle_capacity * veh_obj
            + sw.employee_workload * emp_obj
            + sw.parcel_priority * scores.priority_score_scaled
            - sw.distance * scores.dist_cost_scaled
            - sw.duration * scores.dur_cost_scaled
        )

        return sw
