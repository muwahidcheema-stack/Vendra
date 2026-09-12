from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from ..models.models import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: str | None = None
    avatar_url: str | None = None

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class UserUpdate(BaseModel):
    full_name: str
    avatar_url: str | None = None
    phone: str | None = None

class UserResponse(UserBase):
    id: int
    role: UserRole
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
