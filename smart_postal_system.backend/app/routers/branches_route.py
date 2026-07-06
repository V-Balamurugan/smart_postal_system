from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user_model import User
from app.schemas.branch_schema import (
    BranchCreate,
    BranchResponse,
    BranchUpdate,
)
from app.services.branch_service import BranchService

router = APIRouter(
    prefix="/branches",
    tags=["Branch Management"],
)


# ---------------------------------------------------------
# Create Branch (ADMIN)
# ---------------------------------------------------------
@router.post(
    "/",
    response_model=BranchResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_branch(
    branch: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can create branches.",
        )

    return BranchService.create_branch(db, branch)


# ---------------------------------------------------------
# Get All Branches
# ADMIN / EMPLOYEE / CUSTOMER
# ---------------------------------------------------------
@router.get(
    "/",
    response_model=List[BranchResponse],
)
def get_all_branches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BranchService.get_all_branches(db)


# ---------------------------------------------------------
# Get Branch By ID
# ADMIN / EMPLOYEE / CUSTOMER
# ---------------------------------------------------------
@router.get(
    "/{branch_id}",
    response_model=BranchResponse,
)
def get_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BranchService.get_branch_by_id(db, branch_id)


# ---------------------------------------------------------
# Update Branch (ADMIN)
# ---------------------------------------------------------
@router.put(
    "/{branch_id}",
    response_model=BranchResponse,
)
def update_branch(
    branch_id: int,
    branch: BranchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can update branches.",
        )

    return BranchService.update_branch(
        db=db,
        branch_id=branch_id,
        branch_data=branch,
    )


# ---------------------------------------------------------
# Activate Branch (ADMIN)
# ---------------------------------------------------------
@router.patch(
    "/{branch_id}/activate",
    response_model=BranchResponse,
)
def activate_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can activate branches.",
        )

    return BranchService.activate_branch(db, branch_id)


# ---------------------------------------------------------
# Deactivate Branch (ADMIN)
# ---------------------------------------------------------
@router.patch(
    "/{branch_id}/deactivate",
    response_model=BranchResponse,
)
def deactivate_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can deactivate branches.",
        )

    return BranchService.deactivate_branch(db, branch_id)


# ---------------------------------------------------------
# Delete Branch (ADMIN)
# ---------------------------------------------------------
@router.delete(
    "/{branch_id}",
    status_code=status.HTTP_200_OK,
)
def delete_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can delete branches.",
        )

    return BranchService.delete_branch(db, branch_id)