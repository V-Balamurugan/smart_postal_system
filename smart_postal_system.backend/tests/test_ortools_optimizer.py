"""
Unit Tests: Phase 2 — Google OR-Tools CP-SAT Optimizer
=======================================================

Tests the following components in isolation (no database needed):

1. ``ai_utils``   — helper functions
2. ``variable``   — ORToolsVariableBuilder
3. ``objective``  — PrecomputedScores, ORToolsObjectiveBuilder
4. ``solver``     — ORToolsSolver
5. ``ortools_optimizer`` — ORToolsOptimizer end-to-end

All ORM objects are simple ``SimpleNamespace`` mocks to avoid SQLAlchemy
dependency in the unit-test layer.
"""

from __future__ import annotations

import pytest
from types import SimpleNamespace
from typing import Any, List, Optional

# ---------------------------------------------------------------------------
# Mock ORM helpers
# ---------------------------------------------------------------------------


def _make_vehicle(
    *,
    vehicle_id: int = 1,
    status: str = "AVAILABLE",
    capacity_kg: float = 500.0,
    current_branch_id: int = 1,
) -> SimpleNamespace:
    return SimpleNamespace(
        vehicle_id=vehicle_id,
        status=status,
        capacity_kg=capacity_kg,
        current_branch_id=current_branch_id,
    )


def _make_employee(
    *,
    employee_id: int = 1,
    is_available: bool = True,
    current_workload: int = 0,
    max_workload: int = 20,
) -> SimpleNamespace:
    return SimpleNamespace(
        employee_id=employee_id,
        is_available=is_available,
        current_workload=current_workload,
        max_workload=max_workload,
    )


def _make_parcel(
    *,
    parcel_id: int = 1,
    weight: float = 10.0,
    priority_level: str = "NORMAL",
    delivery_address: str = "123 Main St",
    expected_delivery: Any = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        parcel_id=parcel_id,
        weight=weight,
        priority_level=priority_level,
        delivery_address=delivery_address,
        expected_delivery=expected_delivery,
    )


def _make_route(
    *,
    route_id: int = 1,
    distance_km: float = 50.0,
    estimated_duration_minutes: float = 60.0,
    start_branch_id: int = 1,
) -> SimpleNamespace:
    return SimpleNamespace(
        route_id=route_id,
        distance_km=distance_km,
        estimated_duration_minutes=estimated_duration_minutes,
        start_branch_id=start_branch_id,
    )


DEFAULT_WEIGHTS = {
    "distance": 25.0,
    "duration": 20.0,
    "employee_workload": 20.0,
    "vehicle_capacity": 15.0,
    "parcel_priority": 20.0,
}


# ===========================================================================
# 1. ai_utils tests
# ===========================================================================

class TestAiUtils:

    def test_get_parcel_priority_priority_level_attr(self):
        from app.ai.ai_utils import get_parcel_priority
        p = _make_parcel(priority_level="HIGH")
        assert get_parcel_priority(p) == "HIGH"

    def test_get_parcel_priority_fallback_attr(self):
        from app.ai.ai_utils import get_parcel_priority
        p = SimpleNamespace(priority="MEDIUM")
        assert get_parcel_priority(p) == "MEDIUM"

    def test_get_parcel_priority_default(self):
        from app.ai.ai_utils import get_parcel_priority
        p = SimpleNamespace()
        assert get_parcel_priority(p) == "LOW"

    def test_compute_total_weight(self):
        from app.ai.ai_utils import compute_total_weight
        parcels = [_make_parcel(weight=10.0), _make_parcel(weight=20.0)]
        assert compute_total_weight(parcels) == 30.0

    def test_compute_avg_priority_score_all_high(self):
        from app.ai.ai_utils import compute_avg_priority_score
        parcels = [_make_parcel(priority_level="HIGH")] * 3
        assert compute_avg_priority_score(parcels) == 100.0

    def test_compute_avg_priority_score_mixed(self):
        from app.ai.ai_utils import compute_avg_priority_score
        parcels = [
            _make_parcel(priority_level="HIGH"),   # 100
            _make_parcel(priority_level="LOW"),    #  40
        ]
        assert compute_avg_priority_score(parcels) == 70.0

    def test_is_vehicle_available_string_status(self):
        from app.ai.ai_utils import is_vehicle_available
        assert is_vehicle_available(_make_vehicle(status="AVAILABLE")) is True
        assert is_vehicle_available(_make_vehicle(status="IN_TRANSIT")) is False

    def test_is_vehicle_available_enum_status(self):
        from app.ai.ai_utils import is_vehicle_available
        from types import SimpleNamespace
        v = SimpleNamespace(status=SimpleNamespace(value="AVAILABLE"))
        assert is_vehicle_available(v) is True

    def test_get_vehicle_capacity(self):
        from app.ai.ai_utils import get_vehicle_capacity
        assert get_vehicle_capacity(_make_vehicle(capacity_kg=300.0)) == 300.0

    def test_is_employee_available(self):
        from app.ai.ai_utils import is_employee_available
        assert is_employee_available(_make_employee(is_available=True)) is True
        assert is_employee_available(_make_employee(is_available=False)) is False

    def test_is_employee_workload_ok(self):
        from app.ai.ai_utils import is_employee_workload_ok
        emp = _make_employee(current_workload=10, max_workload=20)
        assert is_employee_workload_ok(emp, 5) is True   # 10+5=15 <= 20
        assert is_employee_workload_ok(emp, 11) is False  # 10+11=21 > 20

    def test_build_optimized_sequence_ordered_by_position(self):
        from app.ai.ai_utils import build_optimized_sequence
        parcels = [
            _make_parcel(parcel_id=1, priority_level="LOW"),
            _make_parcel(parcel_id=2, priority_level="HIGH"),
        ]
        positions = [1, 0]  # parcel 2 should come first
        seq = build_optimized_sequence(parcels, positions)
        assert seq[0]["parcel_id"] == 2
        assert seq[1]["parcel_id"] == 1

    def test_build_optimized_sequence_no_positions(self):
        from app.ai.ai_utils import build_optimized_sequence
        parcels = [_make_parcel(parcel_id=i) for i in range(3)]
        seq = build_optimized_sequence(parcels)
        assert [s["parcel_id"] for s in seq] == [0, 1, 2]

    def test_compute_cost_metrics(self):
        from app.ai.ai_utils import compute_cost_metrics, FUEL_CONSUMPTION_PER_KM, COST_PER_KM
        metrics = compute_cost_metrics(100.0)
        assert metrics["fuel"] == round(100.0 * FUEL_CONSUMPTION_PER_KM, 2)
        assert metrics["cost"] == round(100.0 * COST_PER_KM, 2)


# ===========================================================================
# 2. variable.py tests
# ===========================================================================

class TestORToolsVariableBuilder:

    @pytest.fixture(autouse=True)
    def skip_if_no_ortools(self):
        pytest.importorskip("ortools", reason="ortools not installed")

    def test_variable_counts(self):
        from ortools.sat.python import cp_model
        from app.ai.variable import ORToolsVariableBuilder

        model = cp_model.CpModel()
        var_set = ORToolsVariableBuilder.build(
            model, n_vehicles=3, n_employees=2, n_parcels=4
        )

        assert len(var_set.vehicle_selected) == 3
        assert len(var_set.employee_selected) == 2
        assert len(var_set.parcel_positions) == 4
        assert var_set.n_vehicles == 3
        assert var_set.n_employees == 2
        assert var_set.n_parcels == 4

    def test_variable_set_is_frozen(self):
        from ortools.sat.python import cp_model
        from app.ai.variable import ORToolsVariableBuilder

        model = cp_model.CpModel()
        var_set = ORToolsVariableBuilder.build(
            model, n_vehicles=2, n_employees=2, n_parcels=2
        )
        with pytest.raises((AttributeError, TypeError)):
            var_set.n_vehicles = 99  # type: ignore[misc]

    def test_parcel_position_range(self):
        """Parcel positions must be in [0, n_parcels-1] — validated by solver."""
        from ortools.sat.python import cp_model
        from app.ai.variable import ORToolsVariableBuilder

        model = cp_model.CpModel()
        n = 5
        var_set = ORToolsVariableBuilder.build(
            model, n_vehicles=1, n_employees=1, n_parcels=n
        )
        # Force all positions to be within the expected domain by adding AllDifferent
        model.add_all_different(var_set.parcel_positions)
        model.add_exactly_one(var_set.vehicle_selected)
        model.add_exactly_one(var_set.employee_selected)

        solver = cp_model.CpSolver()
        status = solver.solve(model)
        assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

        positions = [solver.value(var_set.parcel_positions[p]) for p in range(n)]
        assert sorted(positions) == list(range(n))


# ===========================================================================
# 3. objective.py tests
# ===========================================================================

class TestPrecomputedScores:

    def test_vehicle_scores_max_headroom(self):
        """A vehicle with capacity >> total_weight should score near SCALE."""
        from app.ai.objective import PrecomputedScores
        from app.ai.ai_utils import SCALE

        vehicles = [_make_vehicle(capacity_kg=1000.0)]
        parcels = [_make_parcel(weight=1.0)]  # total = 1.0
        route = _make_route(distance_km=10.0, estimated_duration_minutes=15.0)
        employees = [_make_employee()]

        scores = PrecomputedScores.from_inputs(
            vehicles=vehicles, employees=employees,
            parcels=parcels, route=route,
        )
        # headroom = (1000 - 1) / 1000 ≈ 0.999
        assert scores.vehicle_scores[0] >= int(0.99 * SCALE)

    def test_vehicle_scores_zero_when_over_capacity(self):
        """A vehicle with zero spare capacity should score 0."""
        from app.ai.objective import PrecomputedScores

        vehicles = [_make_vehicle(capacity_kg=10.0)]
        parcels = [_make_parcel(weight=20.0)]  # overweight
        route = _make_route()
        employees = [_make_employee()]

        scores = PrecomputedScores.from_inputs(
            vehicles=vehicles, employees=employees,
            parcels=parcels, route=route,
        )
        assert scores.vehicle_scores[0] == 0

    def test_priority_score_scaled(self):
        from app.ai.objective import PrecomputedScores
        from app.ai.ai_utils import SCALE

        parcels = [_make_parcel(priority_level="HIGH")] * 2
        scores = PrecomputedScores.from_inputs(
            vehicles=[_make_vehicle()], employees=[_make_employee()],
            parcels=parcels, route=_make_route(),
        )
        assert scores.priority_score_scaled == int(100 * SCALE)


class TestORToolsObjectiveBuilder:

    @pytest.fixture(autouse=True)
    def skip_if_no_ortools(self):
        pytest.importorskip("ortools", reason="ortools not installed")

    def test_objective_is_added_to_model(self):
        """Solver should find a feasible solution after objective is built."""
        from ortools.sat.python import cp_model
        from app.ai.variable import ORToolsVariableBuilder
        from app.ai.objective import ORToolsObjectiveBuilder, PrecomputedScores

        vehicles = [_make_vehicle(capacity_kg=500.0)]
        employees = [_make_employee()]
        parcels = [_make_parcel(weight=10.0)]
        route = _make_route()

        model = cp_model.CpModel()
        var_set = ORToolsVariableBuilder.build(
            model, n_vehicles=1, n_employees=1, n_parcels=1
        )
        model.add_exactly_one(var_set.vehicle_selected)
        model.add_exactly_one(var_set.employee_selected)

        scores = PrecomputedScores.from_inputs(
            vehicles=vehicles, employees=employees,
            parcels=parcels, route=route,
        )
        ORToolsObjectiveBuilder.build(model, var_set, scores, DEFAULT_WEIGHTS)

        solver = cp_model.CpSolver()
        status = solver.solve(model)
        assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


# ===========================================================================
# 4. solver.py tests
# ===========================================================================

class TestORToolsSolver:

    @pytest.fixture(autouse=True)
    def skip_if_no_ortools(self):
        pytest.importorskip("ortools", reason="ortools not installed")

    def _trivial_feasible_model(self):
        from ortools.sat.python import cp_model
        model = cp_model.CpModel()
        x = model.new_bool_var("x")
        model.add(x == 1)
        return model

    def _trivial_infeasible_model(self):
        from ortools.sat.python import cp_model
        model = cp_model.CpModel()
        x = model.new_bool_var("x")
        model.add(x == 1)
        model.add(x == 0)
        return model

    def test_feasible_model_returns_result(self):
        from app.ai.solver import ORToolsSolver

        solver = ORToolsSolver()
        result = solver.solve(self._trivial_feasible_model())
        assert result.is_feasible is True
        assert result.status_name in ("OPTIMAL", "FEASIBLE")

    def test_infeasible_model_raises_value_error(self):
        from app.ai.solver import ORToolsSolver

        solver = ORToolsSolver()
        with pytest.raises(ValueError, match="no feasible solution"):
            solver.solve(self._trivial_infeasible_model())

    def test_solver_result_is_frozen(self):
        from app.ai.solver import ORToolsSolver

        solver = ORToolsSolver()
        result = solver.solve(self._trivial_feasible_model())
        with pytest.raises((AttributeError, TypeError)):
            result.is_feasible = False  # type: ignore[misc]


# ===========================================================================
# 5. ORToolsOptimizer end-to-end tests
# ===========================================================================

class TestORToolsOptimizerEndToEnd:

    @pytest.fixture(autouse=True)
    def skip_if_no_ortools(self):
        pytest.importorskip("ortools", reason="ortools not installed")

    def _run(self, vehicles, employees, parcels, route=None, weights=None):
        from app.ai.ortools_optimizer import ORToolsOptimizer
        return ORToolsOptimizer.optimize(
            route=route or _make_route(),
            vehicles=vehicles,
            employees=employees,
            parcels=parcels,
            weights=weights or DEFAULT_WEIGHTS,
            use_hybrid=False,
        )

    # --- Happy path ----------------------------------------------------------

    def test_basic_optimization_returns_required_keys(self):
        result = self._run(
            vehicles=[_make_vehicle()],
            employees=[_make_employee()],
            parcels=[_make_parcel()],
        )
        required = {
            "selected_vehicle_id", "selected_employee_id",
            "optimization_score", "estimated_fuel_consumption",
            "estimated_cost", "optimization_algorithm", "solver_status",
            "optimized_sequence", "total_parcels", "score_breakdown",
        }
        assert required.issubset(result.keys())

    def test_algorithm_name_is_ortools(self):
        result = self._run(
            vehicles=[_make_vehicle()],
            employees=[_make_employee()],
            parcels=[_make_parcel()],
        )
        assert result["optimization_algorithm"] == "OR-Tools CP-SAT"

    def test_solver_status_is_optimal_or_feasible(self):
        result = self._run(
            vehicles=[_make_vehicle()],
            employees=[_make_employee()],
            parcels=[_make_parcel()],
        )
        assert result["solver_status"] in ("OPTIMAL", "FEASIBLE")

    def test_selects_correct_vehicle(self):
        """Only vehicle 2 has enough capacity — it must be chosen."""
        vehicles = [
            _make_vehicle(vehicle_id=1, capacity_kg=5.0),   # too small
            _make_vehicle(vehicle_id=2, capacity_kg=500.0), # OK
        ]
        parcels = [_make_parcel(weight=100.0)]
        result = self._run(
            vehicles=vehicles,
            employees=[_make_employee()],
            parcels=parcels,
        )
        assert result["selected_vehicle_id"] == 2

    def test_selects_correct_employee(self):
        """Only employee 2 is available — it must be chosen."""
        employees = [
            _make_employee(employee_id=1, is_available=False),
            _make_employee(employee_id=2, is_available=True),
        ]
        result = self._run(
            vehicles=[_make_vehicle()],
            employees=employees,
            parcels=[_make_parcel()],
        )
        assert result["selected_employee_id"] == 2

    def test_parcel_sequence_length_matches(self):
        parcels = [_make_parcel(parcel_id=i, weight=1.0) for i in range(5)]
        result = self._run(
            vehicles=[_make_vehicle(capacity_kg=1000.0)],
            employees=[_make_employee()],
            parcels=parcels,
        )
        assert len(result["optimized_sequence"]) == 5

    def test_parcel_sequence_positions_are_unique(self):
        parcels = [_make_parcel(parcel_id=i, weight=1.0) for i in range(4)]
        result = self._run(
            vehicles=[_make_vehicle(capacity_kg=1000.0)],
            employees=[_make_employee()],
            parcels=parcels,
        )
        positions = [s["position"] for s in result["optimized_sequence"]]
        assert len(positions) == len(set(positions))

    def test_optimization_score_in_range(self):
        result = self._run(
            vehicles=[_make_vehicle()],
            employees=[_make_employee()],
            parcels=[_make_parcel()],
        )
        assert 0.0 <= result["optimization_score"] <= 100.0

    def test_cost_metrics_are_positive(self):
        result = self._run(
            vehicles=[_make_vehicle()],
            employees=[_make_employee()],
            parcels=[_make_parcel()],
            route=_make_route(distance_km=100.0),
        )
        assert result["estimated_fuel_consumption"] > 0
        assert result["estimated_cost"] > 0

    def test_score_breakdown_keys(self):
        result = self._run(
            vehicles=[_make_vehicle()],
            employees=[_make_employee()],
            parcels=[_make_parcel()],
        )
        bd = result["score_breakdown"]
        assert "vehicle_capacity_headroom" in bd
        assert "employee_workload_headroom" in bd
        assert "avg_parcel_priority_score" in bd
        assert "solver_status" in bd

    # --- Infeasible cases ----------------------------------------------------

    def test_raises_when_no_vehicle_has_capacity(self):
        from app.ai.ortools_optimizer import ORToolsOptimizer
        with pytest.raises(ValueError):
            ORToolsOptimizer.optimize(
                route=_make_route(),
                vehicles=[_make_vehicle(capacity_kg=1.0)],   # 1 kg capacity
                employees=[_make_employee()],
                parcels=[_make_parcel(weight=500.0)],         # 500 kg parcel
                weights=DEFAULT_WEIGHTS,
            )

    def test_raises_when_no_employee_available(self):
        from app.ai.ortools_optimizer import ORToolsOptimizer
        with pytest.raises(ValueError):
            ORToolsOptimizer.optimize(
                route=_make_route(),
                vehicles=[_make_vehicle()],
                employees=[_make_employee(is_available=False)],
                parcels=[_make_parcel()],
                weights=DEFAULT_WEIGHTS,
            )

    def test_raises_when_employee_overloaded(self):
        from app.ai.ortools_optimizer import ORToolsOptimizer
        with pytest.raises(ValueError):
            ORToolsOptimizer.optimize(
                route=_make_route(),
                vehicles=[_make_vehicle()],
                employees=[_make_employee(current_workload=20, max_workload=20)],
                parcels=[_make_parcel(weight=1.0)],
                weights=DEFAULT_WEIGHTS,
            )

    def test_raises_when_empty_inputs(self):
        from app.ai.ortools_optimizer import ORToolsOptimizer
        with pytest.raises(ValueError, match="Insufficient data"):
            ORToolsOptimizer.optimize(
                route=_make_route(),
                vehicles=[],
                employees=[_make_employee()],
                parcels=[_make_parcel()],
                weights=DEFAULT_WEIGHTS,
            )

    # --- Branch constraint ---------------------------------------------------

    def test_vehicle_branch_constraint(self):
        """Vehicle in wrong branch should be excluded; correct one chosen."""
        vehicles = [
            _make_vehicle(vehicle_id=10, current_branch_id=99),  # wrong branch
            _make_vehicle(vehicle_id=11, current_branch_id=1),   # correct
        ]
        route = _make_route(start_branch_id=1)
        result = self._run(
            vehicles=vehicles,
            employees=[_make_employee()],
            parcels=[_make_parcel()],
            route=route,
        )
        assert result["selected_vehicle_id"] == 11

    # --- Multiple candidates — best wins ------------------------------------

    def test_picks_highest_capacity_headroom_vehicle(self):
        """
        When both vehicles satisfy constraints, the one with more headroom
        should be preferred (higher vehicle_capacity weight).
        """
        vehicles = [
            _make_vehicle(vehicle_id=1, capacity_kg=110.0),  # tight headroom
            _make_vehicle(vehicle_id=2, capacity_kg=1000.0), # lots of headroom
        ]
        parcels = [_make_parcel(weight=100.0)]
        weights = {**DEFAULT_WEIGHTS, "vehicle_capacity": 80.0, "distance": 5.0,
                   "duration": 5.0, "employee_workload": 5.0, "parcel_priority": 5.0}
        result = self._run(
            vehicles=vehicles,
            employees=[_make_employee()],
            parcels=parcels,
            weights=weights,
        )
        assert result["selected_vehicle_id"] == 2


# ===========================================================================
# 6. RouteOptimizer dispatch tests
# ===========================================================================

class TestRouteOptimizerDispatch:
    """Verify that RouteOptimizer correctly routes to OR-Tools or fallback."""

    @pytest.fixture(autouse=True)
    def skip_if_no_ortools(self):
        pytest.importorskip("ortools", reason="ortools not installed")

    def test_use_ortools_true_selects_ortools_algorithm(self):
        from app.ai.optimizer import RouteOptimizer

        result = RouteOptimizer.optimize(
            route=_make_route(),
            vehicles=[_make_vehicle()],
            employees=[_make_employee()],
            parcels=[_make_parcel()],
            weights=DEFAULT_WEIGHTS,
            use_ortools=True,
            use_hybrid=False,
        )
        assert result["optimization_algorithm"] == "OR-Tools CP-SAT"

    def test_use_ortools_false_selects_rule_based(self):
        from app.ai.optimizer import RouteOptimizer

        # Rule-based engine runs build_constraint_report which checks:
        #   1. vehicle_branch:  vehicle.current_branch_id == route.start_branch_id
        #   2. employee_branch: employee.branch_id == route.start_branch_id
        #   3. route_valid:     distance > 0 and duration > 0
        route = SimpleNamespace(
            route_id=1,
            distance_km=50.0,
            estimated_duration_minutes=60.0,
            start_branch_id=1,
            start_branch=None,   # no ORM relationship needed for mock
        )
        vehicle = SimpleNamespace(
            vehicle_id=1,
            status="AVAILABLE",
            capacity_kg=500.0,
            current_branch_id=1,
        )
        employee = SimpleNamespace(
            employee_id=1,
            is_available=True,
            current_workload=0,
            max_workload=20,
            branch=None,
            branch_id=1,
        )

        result = RouteOptimizer.optimize(
            route=route,
            vehicles=[vehicle],
            employees=[employee],
            parcels=[_make_parcel()],
            weights=DEFAULT_WEIGHTS,
            use_ortools=False,
            use_hybrid=False,
        )
        assert result["optimization_algorithm"] == "Rule-Based"
