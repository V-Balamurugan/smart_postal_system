from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.parcel_model import Parcel
from app.models.user_model import User
from app.models.employee_model import Employee
from app.models.branch_model import Branch
from app.models.vehicle_model import Vehicle
from app.models.delivery_assignment_model import DeliveryAssignment
from app.models.tracking_model import TrackingHistory

from app.schemas.dashboard_schema import (
    DashboardResponse,
    OverviewStats,
    ParcelStats,
    ParcelStatusCount,
    EmployeeStats,
    VehicleStats,
    BranchStats,
    DeliveryAssignmentStats,
    RecentParcel,
    RecentTrackingActivity,
    TopEmployee,
    PriorityCount,
)


def get_dashboard_data(db: Session) -> DashboardResponse:

    # ─────────────────────────────────────────
    # Overview Counts
    # ─────────────────────────────────────────

    total_parcels = db.query(func.count(Parcel.parcel_id)).scalar() or 0
    total_users = db.query(func.count(User.user_id)).scalar() or 0
    total_employees = db.query(func.count(Employee.employee_id)).scalar() or 0
    total_branches = db.query(func.count(Branch.branch_id)).scalar() or 0
    total_vehicles = db.query(func.count(Vehicle.vehicle_id)).scalar() or 0
    total_assignments = db.query(func.count(DeliveryAssignment.assignment_id)).scalar() or 0

    overview = OverviewStats(
        total_parcels=total_parcels,
        total_users=total_users,
        total_employees=total_employees,
        total_branches=total_branches,
        total_vehicles=total_vehicles,
        total_delivery_assignments=total_assignments,
    )

    # ─────────────────────────────────────────
    # Parcel Stats
    # ─────────────────────────────────────────

    parcel_status_rows = (
        db.query(Parcel.status, func.count(Parcel.parcel_id))
        .group_by(Parcel.status)
        .all()
    )
    status_map = {row[0].upper(): row[1] for row in parcel_status_rows}
    status_breakdown = [ParcelStatusCount(status=s, count=c) for s, c in status_map.items()]

    parcel_stats = ParcelStats(
        total=total_parcels,
        pending=status_map.get("PENDING", 0),
        in_transit=status_map.get("IN_TRANSIT", 0),
        delivered=status_map.get("DELIVERED", 0),
        cancelled=status_map.get("CANCELLED", 0),
        returned=status_map.get("RETURNED", 0),
        status_breakdown=status_breakdown,
    )

    # ─────────────────────────────────────────
    # Employee Stats
    # ─────────────────────────────────────────

    active_employees = (
        db.query(func.count(Employee.employee_id))
        .filter(Employee.status == "ACTIVE")
        .scalar() or 0
    )
    inactive_employees = (
        db.query(func.count(Employee.employee_id))
        .filter(Employee.status != "ACTIVE")
        .scalar() or 0
    )
    available_employees = (
        db.query(func.count(Employee.employee_id))
        .filter(Employee.is_available == True)
        .scalar() or 0
    )
    on_delivery_employees = (
        db.query(func.count(Employee.employee_id))
        .filter(Employee.is_available == False)
        .scalar() or 0
    )

    employee_stats = EmployeeStats(
        total=total_employees,
        active=active_employees,
        inactive=inactive_employees,
        available=available_employees,
        on_delivery=on_delivery_employees,
    )

    # ─────────────────────────────────────────
    # Vehicle Stats
    # ─────────────────────────────────────────

    vehicle_status_rows = (
        db.query(Vehicle.status, func.count(Vehicle.vehicle_id))
        .group_by(Vehicle.status)
        .all()
    )
    vehicle_map = {str(row[0].value).upper(): row[1] for row in vehicle_status_rows}

    vehicle_stats = VehicleStats(
        total=total_vehicles,
        available=vehicle_map.get("AVAILABLE", 0),
        in_transit=vehicle_map.get("IN_TRANSIT", 0),
        maintenance=vehicle_map.get("MAINTENANCE", 0),
        out_of_service=vehicle_map.get("OUT_OF_SERVICE", 0),
    )

    # ─────────────────────────────────────────
    # Branch Stats
    # ─────────────────────────────────────────

    active_branches = (
        db.query(func.count(Branch.branch_id))
        .filter(Branch.is_active == True)
        .scalar() or 0
    )
    inactive_branches = total_branches - active_branches

    branch_stats = BranchStats(
        total=total_branches,
        active=active_branches,
        inactive=inactive_branches,
    )

    # ─────────────────────────────────────────
    # Delivery Assignment Stats
    # ─────────────────────────────────────────

    assign_status_rows = (
        db.query(DeliveryAssignment.assignment_status, func.count(DeliveryAssignment.assignment_id))
        .group_by(DeliveryAssignment.assignment_status)
        .all()
    )
    assign_map = {row[0].upper(): row[1] for row in assign_status_rows}

    delivery_assignment_stats = DeliveryAssignmentStats(
        total=total_assignments,
        assigned=assign_map.get("ASSIGNED", 0),
        in_progress=assign_map.get("IN_PROGRESS", 0),
        completed=assign_map.get("COMPLETED", 0),
        failed=assign_map.get("FAILED", 0),
        cancelled=assign_map.get("CANCELLED", 0),
    )

    # ─────────────────────────────────────────
    # Recent Parcels (last 10)
    # ─────────────────────────────────────────

    recent_parcel_rows = (
        db.query(Parcel)
        .order_by(Parcel.booking_date.desc())
        .limit(10)
        .all()
    )
    recent_parcels = [
        RecentParcel(
            parcel_id=p.parcel_id,
            tracking_number=p.tracking_number,
            status=p.status,
            priority_level=p.priority_level,
            source_branch=p.source_branch,
            destination_branch=p.destination_branch,
            booking_date=str(p.booking_date) if p.booking_date else None,
        )
        for p in recent_parcel_rows
    ]

    # ─────────────────────────────────────────
    # Recent Tracking Activity (last 10)
    # ─────────────────────────────────────────

    recent_tracking_rows = (
        db.query(TrackingHistory)
        .order_by(TrackingHistory.created_at.desc())
        .limit(10)
        .all()
    )
    recent_tracking_activity = [
        RecentTrackingActivity(
            tracking_id=t.tracking_id,
            parcel_id=t.parcel_id,
            status=t.status,
            remarks=t.remarks,
            created_at=str(t.created_at) if t.created_at else None,
        )
        for t in recent_tracking_rows
    ]

    # ─────────────────────────────────────────
    # Top Performing Employees (by completed deliveries)
    # ─────────────────────────────────────────

    top_employee_rows = (
        db.query(
            Employee,
            func.count(DeliveryAssignment.assignment_id).label("completed_count"),
        )
        .join(DeliveryAssignment, DeliveryAssignment.employee_id == Employee.employee_id)
        .filter(DeliveryAssignment.assignment_status == "COMPLETED")
        .group_by(Employee.employee_id)
        .order_by(func.count(DeliveryAssignment.assignment_id).desc())
        .limit(5)
        .all()
    )
    top_employees = [
        TopEmployee(
            employee_id=emp.employee_id,
            employee_code=emp.employee_code,
            designation=emp.designation,
            branch=emp.branch,
            completed_deliveries=count,
        )
        for emp, count in top_employee_rows
    ]

    # ─────────────────────────────────────────
    # Priority Breakdown
    # ─────────────────────────────────────────

    priority_rows = (
        db.query(Parcel.priority_level, func.count(Parcel.parcel_id))
        .group_by(Parcel.priority_level)
        .all()
    )
    priority_breakdown = [
        PriorityCount(priority=row[0], count=row[1]) for row in priority_rows
    ]

    return DashboardResponse(
        overview=overview,
        parcel_stats=parcel_stats,
        employee_stats=employee_stats,
        vehicle_stats=vehicle_stats,
        branch_stats=branch_stats,
        delivery_assignment_stats=delivery_assignment_stats,
        recent_parcels=recent_parcels,
        recent_tracking_activity=recent_tracking_activity,
        top_employees=top_employees,
        priority_breakdown=priority_breakdown,
    )
