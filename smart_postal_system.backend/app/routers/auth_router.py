from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.user_model import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    print("Input username:", form_data.username)
    print("Input password:", form_data.password)

    user = db.query(User).filter(User.email == form_data.username).first()

    print("User Found:", user)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    print("DB Email:", user.email)
    print("Stored Hash:", user.hashed_password)

    password_ok = verify_password(form_data.password, user.hashed_password)
    print("Password Match:", password_ok)

    if not password_ok:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }