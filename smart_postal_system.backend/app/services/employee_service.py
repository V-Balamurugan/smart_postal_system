from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user_model import User
from app.models.employee_model import Employee

from app.schemas.employee_schema import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeLocationUpdate,
    EmployeeAvailabilityUpdate,
)


class EmployeeService:
    @staticmethod
    def generate_employee_code(db: Session) -> str:
        """
        Generate the next employee code.
        Example:
            EMP0001
            EMP0002
        """

        last_employee = (
            db.query(Employee)
            .order_by(Employee.employee_id.desc())
            .first()
        )

        if not last_employee:
            return "EMP0001"

        try:
            last_number = int(last_employee.employee_code.replace("EMP", ""))
        except (ValueError, AttributeError):
            last_number = last_employee.employee_id

        return f"EMP{last_number + 1:04d}"

    @staticmethod
    def create_employee(
        db: Session,
        employee: EmployeeCreate,
    ) -> Employee:

        user = (
            db.query(User)
            .filter(User.user_id == employee.user_id)
            .first()
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.role.upper() != "EMPLOYEE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected user is not an EMPLOYEE.",
            )

        existing_employee = (
            db.query(Employee)
            .filter(Employee.user_id == employee.user_id)
            .first()
        )

        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee profile already exists.",
            )

        if employee.vehicle_number:
            existing_vehicle = (
                db.query(Employee)
                .filter(Employee.vehicle_number == employee.vehicle_number)
                .first()
            )

            if existing_vehicle:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Vehicle number already assigned.",
                )

        new_employee = Employee(
            user_id=employee.user_id,
            employee_code=EmployeeService.generate_employee_code(db),
            designation=employee.designation,
            branch=employee.branch,
            vehicle_type=employee.vehicle_type,
            vehicle_number=employee.vehicle_number,
            max_workload=employee.max_workload,
        )

        try:
            db.add(new_employee)
            db.commit()
            db.refresh(new_employee)
            return new_employee

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error while creating employee.",
            )

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_all_employees(db: Session) -> list[Employee]:
        return (
            db.query(Employee)
            .order_by(Employee.employee_id)
            .all()
        )

    @staticmethod
    def get_employee_by_id(
        db: Session,
        employee_id: int,
    ) -> Employee:

        employee = (
            db.query(Employee)
            .filter(Employee.employee_id == employee_id)
            .first()
        )

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found.",
            )

        return employee

    @staticmethod
    def update_employee(
        db: Session,
        employee_id: int,
        employee_data: EmployeeUpdate,
    ) -> Employee:

        employee = EmployeeService.get_employee_by_id(
            db,
            employee_id,
        )

        update_data = employee_data.model_dump(exclude_unset=True)

        if (
            "vehicle_number" in update_data
            and update_data["vehicle_number"] is not None
        ):
            duplicate = (
                db.query(Employee)
                .filter(
                    Employee.vehicle_number == update_data["vehicle_number"],
                    Employee.employee_id != employee_id,
                )
                .first()
            )

            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Vehicle number already assigned.",
                )

        for key, value in update_data.items():
            setattr(employee, key, value)

        try:
            db.commit()
            db.refresh(employee)
            return employee

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to update employee.",
            )

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def delete_employee(
        db: Session,
        employee_id: int,
    ) -> dict:

        employee = EmployeeService.get_employee_by_id(
            db,
            employee_id,
        )

        employee.status = "INACTIVE"

        try:
            db.commit()

        except Exception:
            db.rollback()
            raise

        return {
            "message": "Employee deactivated successfully."
        }

    @staticmethod
    def update_location(
        db: Session,
        employee_id: int,
        location: EmployeeLocationUpdate,
    ) -> Employee:

        employee = EmployeeService.get_employee_by_id(
            db,
            employee_id,
        )

        employee.latitude = location.latitude
        employee.longitude = location.longitude

        try:
            db.commit()
            db.refresh(employee)
            return employee

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def update_availability(
        db: Session,
        employee_id: int,
        availability: EmployeeAvailabilityUpdate,
    ) -> Employee:

        employee = EmployeeService.get_employee_by_id(
            db,
            employee_id,
        )

        employee.is_available = availability.is_available

        try:
            db.commit()
            db.refresh(employee)
            return employee

        except Exception:
            db.rollback()
            raise