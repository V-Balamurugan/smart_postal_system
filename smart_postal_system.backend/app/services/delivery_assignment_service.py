from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.parcel_model import Parcel
from app.models.employee_model import Employee
from app.models.delivery_assignment_model import DeliveryAssignment

from app.schemas.delivery_assignment_schema import (
    DeliveryAssignmentCreate,
    DeliveryAssignmentUpdate,
    AssignmentStatusUpdate,
)


class DeliveryAssignmentService:

    # -----------------------------------------
    # Create Assignment
    # -----------------------------------------
    @staticmethod
    def create_assignment(
        db: Session,
        assignment: DeliveryAssignmentCreate,
        assigned_by: int,
    ):

        parcel = (
            db.query(Parcel)
            .filter(Parcel.parcel_id == assignment.parcel_id)
            .first()
        )

        if not parcel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parcel not found."
            )

        employee = (
            db.query(Employee)
            .filter(Employee.employee_id == assignment.employee_id)
            .first()
        )

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found."
            )

        if employee.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee is inactive."
            )

        if not employee.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee is unavailable."
            )

        if employee.current_workload >= employee.max_workload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee workload exceeded."
            )

        existing = (
            db.query(DeliveryAssignment)
            .filter(
                DeliveryAssignment.parcel_id == assignment.parcel_id
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parcel already assigned."
            )

        new_assignment = DeliveryAssignment(
            parcel_id=assignment.parcel_id,
            employee_id=assignment.employee_id,
            assigned_by=assigned_by,
            priority=assignment.priority,
            remarks=assignment.remarks,
        )

        employee.current_workload += 1

        parcel.status = "ASSIGNED"

        try:
            db.add(new_assignment)
            db.commit()
            db.refresh(new_assignment)

        except Exception:
            db.rollback()
            raise

        return new_assignment

    # -----------------------------------------
    # Get All Assignments
    # -----------------------------------------
    @staticmethod
    def get_all_assignments(db: Session):

        return (
            db.query(DeliveryAssignment)
            .order_by(
                DeliveryAssignment.assignment_id.desc()
            )
            .all()
        )

    # -----------------------------------------
    # Get Assignment By ID
    # -----------------------------------------
    @staticmethod
    def get_assignment_by_id(
        db: Session,
        assignment_id: int,
    ):

        assignment = (
            db.query(DeliveryAssignment)
            .filter(
                DeliveryAssignment.assignment_id
                == assignment_id
            )
            .first()
        )

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found."
            )

        return assignment

    # -----------------------------------------
    # Get Assignments By Employee
    # -----------------------------------------
    @staticmethod
    def get_employee_assignments(
        db: Session,
        employee_id: int,
    ):

        return (
            db.query(DeliveryAssignment)
            .filter(
                DeliveryAssignment.employee_id
                == employee_id
            )
            .all()
        )

    # -----------------------------------------
    # Update Assignment
    # -----------------------------------------
    @staticmethod
    def update_assignment(
        db: Session,
        assignment_id: int,
        assignment_data: DeliveryAssignmentUpdate,
    ):

        assignment = DeliveryAssignmentService.get_assignment_by_id(
            db,
            assignment_id,
        )

        update_data = assignment_data.model_dump(
            exclude_unset=True
        )

        if "employee_id" in update_data:

            new_employee = (
                db.query(Employee)
                .filter(
                    Employee.employee_id
                    == update_data["employee_id"]
                )
                .first()
            )

            if not new_employee:
                raise HTTPException(
                    status_code=404,
                    detail="Employee not found."
                )

            assignment.employee.current_workload -= 1
            new_employee.current_workload += 1

        for key, value in update_data.items():
            setattr(assignment, key, value)

        try:
            db.commit()
            db.refresh(assignment)

        except Exception:
            db.rollback()
            raise

        return assignment

    # -----------------------------------------
    # Update Assignment Status
    # -----------------------------------------
    @staticmethod
    def update_status(
        db: Session,
        assignment_id: int,
        status_data: AssignmentStatusUpdate,
    ):

        assignment = DeliveryAssignmentService.get_assignment_by_id(
            db,
            assignment_id,
        )

        assignment.assignment_status = (
            status_data.assignment_status
        )

        assignment.parcel.status = (
            status_data.assignment_status
        )

        if status_data.assignment_status in [
            "DELIVERED",
            "CANCELLED",
            "FAILED",
        ]:

            if assignment.employee.current_workload > 0:
                assignment.employee.current_workload -= 1

        try:
            db.commit()
            db.refresh(assignment)

        except Exception:
            db.rollback()
            raise

        return assignment

    # -----------------------------------------
    # Delete Assignment
    # -----------------------------------------
    @staticmethod
    def delete_assignment(
        db: Session,
        assignment_id: int,
    ):

        assignment = DeliveryAssignmentService.get_assignment_by_id(
            db,
            assignment_id,
        )

        if assignment.employee.current_workload > 0:
            assignment.employee.current_workload -= 1

        db.delete(assignment)

        try:
            db.commit()

        except Exception:
            db.rollback()
            raise

        return {
            "message": "Assignment deleted successfully."
        }