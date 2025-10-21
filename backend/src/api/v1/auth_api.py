from fastapi import APIRouter, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from src.services.auth_service import create_user, get_user, update_user, delete_user
from src.services.auth_service import authenticate_user, create_access_token, verify_access_token
from src.models.auth_model import User, UserLogin, UserUpdate, Token

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/users/", response_model=bool)
def api_create_user(user_data: User) -> bool:
    success = create_user(user_data)
    if not success:
        raise HTTPException(status_code=400, detail="User creation failed")
    return success

@router.get("/users/{user_id}", response_model=dict)
def api_get_user(user_id: str) -> dict:
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=bool)
def api_update_user(user_id: str, update_data: UserUpdate) -> bool:
    success = update_user(user_id, update_data.dict(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=400, detail="User update failed")
    return success

@router.delete("/users/{user_id}", response_model=bool)
def api_delete_user(user_id: str) -> bool:
    success = delete_user(user_id)
    if not success:
        raise HTTPException(status_code=400, detail="User deletion failed")
    return success

@router.post("/login/", response_model=Token)
def api_login(login_data: UserLogin) -> Token:
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token_data = {"user_id": user["user_id"], "username": user["username"]}
    access_token = create_access_token(token_data)
    return Token(access_token=access_token, token_type="bearer")

@router.post("/verify-token/", response_model=dict)
def api_verify_token(token: str) -> dict:
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


