"""
AI Optimization Utilities
=========================

Shared helper functions used by **both** the Rule-Based (Phase 1) and
OR-Tools CP-SAT (Phase 2) optimization engines.

Consolidating these here avoids duplication between ``constrains.py``,
``scoring.py``, and ``ortools_optimizer.py``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Priority maps
# ---------------------------------------------------------------------------

PRIORITY_SCORE: Dict[str, int] = {
    "HIGH":   100,
    "MEDIUM":  70,
    "NORMAL":  70,
    "LOW":     40,
}

PRIORITY_ORDER: Dict[str, int] = {
    "HIGH":   3,
    "MEDIUM": 2,
    "NORMAL": 2,
    "LOW":    1,
}

# ---------------------------------------------------------------------------
# Cost constants
# ---------------------------------------------------------------------------

FUEL_CONSUMPTION_PER_KM: float = 0.12   # Liters / km
COST_PER_KM: float = 12.5               # Currency / km

# Integer scale factor: multiplies floats → integers for CP-SAT
SCALE: int = 1000


# ---------------------------------------------------------------------------
# Parcel helpers
# ---------------------------------------------------------------------------

def get_parcel_priority(parcel: Any) -> str:
    """Return the priority string for a parcel ORM object."""
    return getattr(parcel, "priority_level", getattr(parcel, "priority", "LOW"))


def get_parcel_weight(parcel: Any) -> float:
    """Return the weight in kg for a parcel ORM object."""
    return float(getattr(parcel, "weight", 0.0))


def compute_total_weight(parcels: List[Any]) -> float:
    """Sum of all parcel weights."""
    return sum(get_parcel_weight(p) for p in parcels)


def compute_avg_priority_score(parcels: List[Any]) -> float:
    """Average priority score (0-100 scale) across all parcels."""
    if not parcels:
        return 0.0
    total = sum(PRIORITY_SCORE.get(get_parcel_priority(p), 40) for p in parcels)
    return total / len(parcels)


# ---------------------------------------------------------------------------
# Vehicle helpers
# ---------------------------------------------------------------------------

def is_vehicle_available(vehicle: Any) -> bool:
    """Check whether a vehicle's status is AVAILABLE."""
    status = getattr(vehicle, "status", None)
    if status is not None:
        return status == "AVAILABLE" or getattr(status, "value", None) == "AVAILABLE"
    return bool(getattr(vehicle, "is_available", False))


def get_vehicle_capacity(vehicle: Any) -> float:
    """Return vehicle capacity in kg."""
    return float(getattr(vehicle, "capacity_kg", getattr(vehicle, "capacity", 0.0)))


def get_vehicle_branch(vehicle: Any) -> Optional[int]:
    """Return the branch ID where the vehicle is currently located."""
    return getattr(vehicle, "current_branch_id", getattr(vehicle, "branch_id", None))


# ---------------------------------------------------------------------------
# Employee helpers
# ---------------------------------------------------------------------------

def is_employee_available(employee: Any) -> bool:
    """Check whether an employee is available for assignment."""
    return bool(getattr(employee, "is_available", False))


def is_employee_workload_ok(employee: Any, n_parcels: int) -> bool:
    """Check whether assigning *n_parcels* would exceed the employee's max."""
    current = getattr(employee, "current_workload", 0)
    maximum = getattr(employee, "max_workload", 0)
    return (current + n_parcels) <= maximum


# ---------------------------------------------------------------------------
# Route helpers
# ---------------------------------------------------------------------------

def get_route_distance(route: Any) -> float:
    """Return route distance in km."""
    return float(getattr(route, "distance_km", getattr(route, "distance", 0.0)))


def get_route_duration(route: Any) -> float:
    """Return route estimated duration in minutes."""
    return float(
        getattr(route, "estimated_duration_minutes",
                getattr(route, "estimated_duration", 0.0))
    )


def get_route_start_branch_id(route: Any) -> Optional[int]:
    """Return the start branch ID of a route."""
    return getattr(route, "start_branch_id", None)


# ---------------------------------------------------------------------------
# Result builders
# ---------------------------------------------------------------------------

def build_optimized_sequence(
    parcels: List[Any],
    positions: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """
    Build the ``optimized_sequence`` list of dicts for the API response.

    Parameters
    ----------
    parcels : list
        ORM parcel objects, in whatever order.
    positions : list[int] | None
        If provided, each entry is the delivery-position index for the
        corresponding parcel.  If None, uses the natural enumerate index.
    """
    sequence = []
    for idx, parcel in enumerate(parcels):
        pos = positions[idx] if positions is not None else idx
        sequence.append({
            "position":    pos,
            "parcel_id":   parcel.parcel_id,
            "priority":    get_parcel_priority(parcel),
            "destination": getattr(
                parcel,
                "delivery_address",
                getattr(parcel, "destination_address", None),
            ),
            "weight_kg":   get_parcel_weight(parcel),
        })
    # Sort by position for readability
    sequence.sort(key=lambda x: x["position"])
    return sequence


def compute_cost_metrics(distance_km: float) -> Dict[str, float]:
    """
    Return fuel consumption and total cost for the given distance.
    """
    return {
        "fuel": round(distance_km * FUEL_CONSUMPTION_PER_KM, 2),
        "cost": round(distance_km * COST_PER_KM, 2),
    }
