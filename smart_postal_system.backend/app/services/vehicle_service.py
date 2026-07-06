from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.branch_model import Branch
from app.models.employee_model import Employee
from app.models.vehicle_model import Vehicle, VehicleStatus

from app.schemas.vehicle_schema import (
    VehicleCreate,
    VehicleUpdate,
)


class VehicleService:

    @staticmethod
    def create_vehicle(
        db: Session,
        vehicle: VehicleCreate,
    ) -> Vehicle:
        """
        Create a new vehicle.
        """

        # Check duplicate vehicle number
        existing_vehicle = (
            db.query(Vehicle)
            .filter(
                Vehicle.vehicle_number == vehicle.vehicle_number
            )
            .first()
        )

        if existing_vehicle:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vehicle number already exists.",
            )

        # Check Branch
        branch = (
            db.query(Branch)
            .filter(
                Branch.id == vehicle.current_branch_id
            )
            .first()
        )

        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found.",
            )

        new_vehicle = Vehicle(**vehicle.model_dump())

        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)

        return new_vehicle

    @staticmethod
    def get_all_vehicles(db: Session):
        return (
            db.query(Vehicle)
            .order_by(Vehicle.vehicle_id)
            .all()
        )

    @staticmethod
    def get_vehicle_by_id(
        db: Session,
        vehicle_id: int,
    ) -> Vehicle:

        vehicle = (
            db.query(Vehicle)
            .filter(
                Vehicle.vehicle_id == vehicle_id
            )
            .first()
        )

        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found.",
            )

        return vehicle

    @staticmethod
    def update_vehicle(
        db: Session,
        vehicle_id: int,
        vehicle_data: VehicleUpdate,
    ) -> Vehicle:

        vehicle = VehicleService.get_vehicle_by_id(
            db,
            vehicle_id,
        )

        update_data = vehicle_data.model_dump(
            exclude_unset=True
        )

        # Duplicate Vehicle Number
        if "vehicle_number" in update_data:

            existing = (
                db.query(Vehicle)
                .filter(
                    Vehicle.vehicle_number == update_data["vehicle_number"],
                    Vehicle.vehicle_id != vehicle_id,
                )
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Vehicle number already exists.",
                )

        # Validate Branch
        if "current_branch_id" in update_data:

            branch = (
                db.query(Branch)
                .filter(
                    Branch.id == update_data["current_branch_id"]
                )
                .first()
            )

            if not branch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Branch not found.",
                )

        for key, value in update_data.items():
            setattr(vehicle, key, value)

        db.commit()
        db.refresh(vehicle)

        return vehicle

    @staticmethod
    def assign_driver(
        db: Session,
        vehicle_id: int,
        driver_id: int,
    ) -> Vehicle:

        vehicle = VehicleService.get_vehicle_by_id(
            db,
            vehicle_id,
        )

        driver = (
            db.query(Employee)
            .filter(
                Employee.employee_id == driver_id
            )
            .first()
        )

        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found.",
            )

        vehicle.driver_id = driver_id

        db.commit()
        db.refresh(vehicle)

        return vehicle

    @staticmethod
    def update_vehicle_status(
        db: Session,
        vehicle_id: int,
        vehicle_status: VehicleStatus,
    ) -> Vehicle:

        vehicle = VehicleService.get_vehicle_by_id(
            db,
            vehicle_id,
        )

        vehicle.status = vehicle_status

        db.commit()
        db.refresh(vehicle)

        return vehicle

    @staticmethod
    def delete_vehicle(
        db: Session,
        vehicle_id: int,
    ):

        vehicle = VehicleService.get_vehicle_by_id(
            db,
            vehicle_id,
        )

        db.delete(vehicle)
        db.commit()

        return {
            "message": "Vehicle deleted successfully."
        }