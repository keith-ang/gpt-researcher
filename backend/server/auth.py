import jwt
import re
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext

from .models import (User, UserCreate)
from .mongodb_config import (db, mongodb_settings)

# <-- Utility functions for authentication -->

ALGORITHM = "HS256"

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

async def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Authenticate the user by checking the email and password.
    """
    user = await db['users'].find_one({"email": email})  
    if not user or not verify_password(password, user["hashed_password"]):
        return None

    # Convert the MongoDB user document to a User model instance
    # This removes the sensitive data like the hashed password
    user_data = {
        "username": user["username"],
        "email": user["email"],
        "organisation_name": user["organisation_name"]
    }

    return User(**user_data)

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token containing the user information and expiration.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, mongodb_settings.SECRET_KEY, algorithm=ALGORITHM)

async def register_user(user_create: UserCreate) -> dict:
    """
    Register a new user in MongoDB.

    - Checks if the email already exists.
    - Hashes the password before storing.
    - Returns the newly created user data.
    """
    # Check if password and confirm_password match
    if user_create.password != user_create.confirm_password:
        raise ValueError("Passwords do not match")

    # Check if user already exists
    existing_user = await db['users'].find_one({"email": user_create.email})
    if existing_user:
        raise ValueError("Email already registered")

    # Validate the password strength
    if not is_valid_password(user_create.password):
        raise ValueError("Password is not strong enough")

    # Hash the password
    hashed_password = get_password_hash(user_create.password)

    # Create user record
    user_data = {
        "username": user_create.username,
        "email": user_create.email,
        "organisation_name": user_create.organisation_name,
        "hashed_password": hashed_password,
    }

    # Insert the new user into the database
    result = await db['users'].insert_one(user_data)
    user_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string for serialization
    
    return User(**user_data)  # Return the User model for client
