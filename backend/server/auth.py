import jwt
import re
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext

from .mongodb_config import (db, mongodb_settings)

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that the provided password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)

def is_valid_password(password: str) -> bool:
    return (
        re.search(r"[A-Z]", password) is not None and
        re.search(r"[a-z]", password) is not None and
        re.search(r"[0-9]", password) is not None and
        re.search(r"[@$!%*?&#]", password) is not None and
        len(password) >= 6
    )

async def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Authenticate the user by checking the email and password.
    """
    user = await db['users'].find_one({"email": email})  
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token containing the user information and expiration.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, mongodb_settings.SECRET_KEY, algorithm="HS256")

async def register_user(username: str, password: str, email: str, organisation_name: str) -> dict:
    """
    Register a new user in MongoDB.
    
    - Checks if the username already exists.
    - Hashes the password before storing.
    - Returns the newly created user data.
    """
    # Check if user already exists
    existing_user = await db['users'].find_one({"email": email})
    if existing_user:
        raise ValueError("Email already registered")
    
    # Hash the password
    hashed_password = get_password_hash(password)
    
    # Create user record
    user_data = {
        "username": username,
        "email": email,
        "organisation_name": organisation_name,
        "hashed_password": hashed_password,
    }
    
    # Insert the new user into the database
    result = await db['users'].insert_one(user_data)
    user_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string for serialization
    return user_data
