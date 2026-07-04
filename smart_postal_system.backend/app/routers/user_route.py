from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserResponse
from app.services.user_service import create_user, get_all_users
from app.core.dependencies import get_current_user, role_required

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# Register User
@router.post("/", response_model=UserResponse)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    return create_user(db, user)


# Admin Only
@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin"]))
):
    return get_all_users(db)


# Current User
@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


# Admin Dashboard
@router.get("/admin-dashboard")
def admin_dashboard(
    current_user: User = Depends(role_required(["ADMIN"]))
):
    return {
        "message": "Welcome Admin",
        "user": current_user.name
    }


# Employee Dashboard
@router.get("/employee-dashboard")
def employee_dashboard(
    current_user: User = Depends(role_required(["EMPLOYEE"]))
):
    return {
        "message": "Welcome Employee",
        "user": current_user.name
    }


# Customer Dashboard
@router.get("/customer-dashboard")
def customer_dashboard(
    current_user: User = Depends(role_required(["CUSTOMER"]))
):
    return {
        "message": "Welcome Customer",
        "user": current_user.name
    }