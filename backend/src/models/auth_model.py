from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
