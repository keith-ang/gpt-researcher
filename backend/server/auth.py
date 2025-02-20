from datetime import datetime, timedelta
from typing import Optional, Dict

import jwt
from passlib.context import CryptContext

# Constants
SECRET_KEY = "YOUR_SECRET_KEY"  # Replace with your actual secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory "database" for demonstration purposes.
placeholder_users_db: Dict[str, dict] = {
    "test@example.com": {
        "username": "test",
        "email": "test@example.com",
        "organisation_name": "Quest Edtech",
        "hashed_password": "$2b$12$rkpI5YmWuZMeufeMPziiU.Jdg.qpWGE1t.qk1XDdDnLyqwsFPvBMW"   # bcrypt hash of "password123"
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Debug check
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def get_user_from_db(username: str) -> Optional[dict]:
    """
    Retrieve a user record from the in-memory database.
    """
    return placeholder_users_db.get(username)

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate the user by checking the username and password.
    """
    user = get_user_from_db(username)
    print(user)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token with an expiration time.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
