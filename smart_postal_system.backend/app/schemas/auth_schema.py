from pydantic import BaseModel, EmailStr


# -----------------------------
# Register Request
# -----------------------------
class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    role: str
    address: str


# -----------------------------
# Login Request
# -----------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# -----------------------------
# JWT Token Response
# -----------------------------
class Token(BaseModel):
    access_token: str
    token_type: str


# -----------------------------
# JWT Payload
# -----------------------------
class TokenData(BaseModel):
    email: str | None = None