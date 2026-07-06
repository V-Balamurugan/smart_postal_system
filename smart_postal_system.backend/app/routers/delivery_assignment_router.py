from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.core.dependencies import get_current_user

from app.models.user_model import User

from app.schemas.delivery_assignment_schema import (
    DeliveryAssignmentCreate,
    DeliveryAssignmentUpdate,
    AssignmentStatusUpdate,
    DeliveryAssignmentResponse,
)

from app.services.delivery_assignment_service import (
    DeliveryAssignmentService,
)


router = APIRouter(
    prefix="/delivery-assignments",
    tags=["Delivery Assignment"],
)


# -------------------------------------------------
# Create Assignment (ADMIN)
# -------------------------------------------------
@router.post(
    "/",
    response_model=DeliveryAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(
    assignment: DeliveryAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can assign parcels.",
        )

    return DeliveryAssignmentService.create_assignment(
        db=db,
        assignment=assignment,
        assigned_by=current_user.user_id,
    )


# -------------------------------------------------
# Get All Assignments
# -------------------------------------------------
@router.get(
    "/",
    response_model=list[DeliveryAssignmentResponse],
)
def get_all_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role not in ["ADMIN", "EMPLOYEE"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    return DeliveryAssignmentService.get_all_assignments(db)


# -------------------------------------------------
# Get Assignment By ID
# -------------------------------------------------
@router.get(
    "/{assignment_id}",
    response_model=DeliveryAssignmentResponse,
)
def get_assignment_by_id(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role not in ["ADMIN", "EMPLOYEE"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    return DeliveryAssignmentService.get_assignment_by_id(
        db,
        assignment_id,
    )


# -------------------------------------------------
# Get Assignments Of One Employee
# -------------------------------------------------
@router.get(
    "/employee/{employee_id}",
    response_model=list[DeliveryAssignmentResponse],
)
def get_employee_assignments(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role not in ["ADMIN", "EMPLOYEE"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    return DeliveryAssignmentService.get_employee_assignments(
        db,
        employee_id,
    )


# -------------------------------------------------
# Update Assignment
# -------------------------------------------------
@router.put(
    "/{assignment_id}",
    response_model=DeliveryAssignmentResponse,
)
def update_assignment(
    assignment_id: int,
    assignment: DeliveryAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can update assignments.",
        )

    return DeliveryAssignmentService.update_assignment(
        db,
        assignment_id,
        assignment,
    )


# -------------------------------------------------
# Update Assignment Status
# -------------------------------------------------
@router.patch(
    "/{assignment_id}/status",
    response_model=DeliveryAssignmentResponse,
)
def update_assignment_status(
    assignment_id: int,
    assignment_status: AssignmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role not in ["ADMIN", "EMPLOYEE"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    return DeliveryAssignmentService.update_status(
        db,
        assignment_id,
        assignment_status,
    )


# -------------------------------------------------
# Delete Assignment
# -------------------------------------------------
@router.delete(
    "/{assignment_id}",
)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can delete assignments.",
        )

    return DeliveryAssignmentService.delete_assignment(
        db,
        assignment_id,
    )