import jwt
import bcrypt
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from src.models.auth_model import User, UserLogin, UserUpdate, Token
from src.database.mongo_client import client

load_dotenv()
secret_key = os.getenv("SECRET_KEY")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_user(user_data: User) -> bool:
    try:
        user_dict = user_data.dict()
        # Hash the password before storing
        user_dict['password'] = hash_password(user_dict['password'])
        return client.create_user(user_dict)
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def get_user(user_id: str) -> dict:
    try:
        return client.get_user(user_id)
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def update_user(user_id: str, update_data: dict) -> bool:
    try:
        # If password is being updated, hash it
        if 'password' in update_data:
            update_data['password'] = hash_password(update_data['password'])
        return client.update_user(user_id, update_data)
    except Exception as e:
        print(f"Error updating user: {e}")
        return False

def delete_user(user_id: str) -> bool:
    try:
        return client.delete_user(user_id)
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False

def authenticate_user(username: str, password: str) -> dict:
    try:
        users_collection = client.db.get_collection("users")
        user = users_collection.find_one({"username": username})
        if user and verify_password(password, user["password"]):
            return user
        return None
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)  # Default 24 hours
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return token

def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
