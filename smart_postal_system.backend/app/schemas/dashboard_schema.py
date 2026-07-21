from pydantic import BaseModel
from typing import Optional


# ─────────────────────────────────────────
# Summary Counts
# ─────────────────────────────────────────

class ParcelStatusCount(BaseModel):
    status: str
    count: int


class OverviewStats(BaseModel):
    total_parcels: int
    total_users: int
    total_employees: int
    total_branches: int
    total_vehicles: int
    total_delivery_assignments: int


# ─────────────────────────────────────────
# Parcel Stats
# ─────────────────────────────────────────

class ParcelStats(BaseModel):
    total: int
    pending: int
    in_transit: int
    delivered: int
    cancelled: int
    returned: int
    status_breakdown: list[ParcelStatusCount]


# ─────────────────────────────────────────
# Employee Stats
# ─────────────────────────────────────────

class EmployeeStats(BaseModel):
    total: int
    active: int
    inactive: int
    available: int
    on_delivery: int


# ─────────────────────────────────────────
# Vehicle Stats
# ─────────────────────────────────────────

class VehicleStats(BaseModel):
    total: int
    available: int
    in_transit: int
    maintenance: int
    out_of_service: int


# ─────────────────────────────────────────
# Branch Stats
# ─────────────────────────────────────────

class BranchStats(BaseModel):
    total: int
    active: int
    inactive: int


# ─────────────────────────────────────────
# Delivery Assignment Stats
# ─────────────────────────────────────────

class DeliveryAssignmentStats(BaseModel):
    total: int
    assigned: int
    in_progress: int
    completed: int
    failed: int
    cancelled: int


# ─────────────────────────────────────────
# Recent Activity
# ─────────────────────────────────────────

class RecentParcel(BaseModel):
    parcel_id: int
    tracking_number: str
    status: str
    priority_level: str
    source_branch: str
    destination_branch: str
    booking_date: Optional[str] = None

    class Config:
        from_attributes = True


class RecentTrackingActivity(BaseModel):
    tracking_id: int
    parcel_id: int
    status: str
    remarks: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# Top Performing Employees
# ─────────────────────────────────────────

class TopEmployee(BaseModel):
    employee_id: int
    employee_code: str
    designation: str
    branch: str
    completed_deliveries: int


# ─────────────────────────────────────────
# Parcel Priority Breakdown
# ─────────────────────────────────────────

class PriorityCount(BaseModel):
    priority: str
    count: int


# ─────────────────────────────────────────
# Full Dashboard Response
# ─────────────────────────────────────────

class DashboardResponse(BaseModel):
    overview: OverviewStats
    parcel_stats: ParcelStats
    employee_stats: EmployeeStats
    vehicle_stats: VehicleStats
    branch_stats: BranchStats
    delivery_assignment_stats: DeliveryAssignmentStats
    recent_parcels: list[RecentParcel]
    recent_tracking_activity: list[RecentTrackingActivity]
    top_employees: list[TopEmployee]
    priority_breakdown: list[PriorityCount]
