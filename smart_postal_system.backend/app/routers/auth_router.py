from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user_model import User
from app.schemas.auth_schema import LoginRequest, Token
from app.core.security import (
    verify_password,
    create_access_token
)
from app.core.config import settings

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/login", response_model=Token)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == request.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(
        request.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }