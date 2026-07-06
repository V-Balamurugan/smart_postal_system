from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.employee_schema import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeLocationUpdate,
    EmployeeAvailabilityUpdate
)

from app.services.employee_service import EmployeeService

from app.core.dependencies import get_current_user

from app.models.user_model import User


router = APIRouter(
    prefix="/employees",
    tags=["Employee Management"]
)


# -----------------------------------------
# Create Employee (ADMIN)
# -----------------------------------------
@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can create employees."
        )

    return EmployeeService.create_employee(db, employee)


# -----------------------------------------
# Get All Employees
# -----------------------------------------
@router.get(
    "/",
    response_model=list[EmployeeResponse]
)
def get_all_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role not in ["ADMIN", "EMPLOYEE"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    return EmployeeService.get_all_employees(db)


# -----------------------------------------
# Get Employee By ID
# -----------------------------------------
@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role not in ["ADMIN", "EMPLOYEE"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    return EmployeeService.get_employee_by_id(
        db,
        employee_id
    )


# -----------------------------------------
# Update Employee
# -----------------------------------------
@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def update_employee(
    employee_id: int,
    employee: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN can update employee."
        )

    return EmployeeService.update_employee(
        db,
        employee_id,
        employee
    )


# -----------------------------------------
# Delete Employee
# -----------------------------------------
@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN can delete employee."
        )

    return EmployeeService.delete_employee(
        db,
        employee_id
    )


# -----------------------------------------
# Update Employee Location
# -----------------------------------------
@router.patch(
    "/{employee_id}/location",
    response_model=EmployeeResponse
)
def update_location(
    employee_id: int,
    location: EmployeeLocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role not in ["ADMIN", "EMPLOYEE"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    return EmployeeService.update_location(
        db,
        employee_id,
        location
    )


# -----------------------------------------
# Update Availability
# -----------------------------------------
@router.patch(
    "/{employee_id}/availability",
    response_model=EmployeeResponse
)
def update_availability(
    employee_id: int,
    availability: EmployeeAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role not in ["ADMIN", "EMPLOYEE"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    return EmployeeService.update_availability(
        db,
        employee_id,
        availability
    )