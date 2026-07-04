from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    role: str = "CUSTOMER"
    address: str


class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    phone: str
    role: str
    address: str

    class Config:
        from_attributes = True