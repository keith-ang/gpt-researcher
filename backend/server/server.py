import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext

from fastapi import (
    FastAPI,
    Request,
    WebSocket,
    WebSocketDisconnect,
    File,
    UploadFile,
    Header,
    HTTPException,
    status,
    Depends,
    Response,
    Cookie
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Import models from models.py
from .models import (
    ResearchRequest,
    ConfigRequest,
    User,
    UserInDB,
    UserCreate,
    Token
)

# Import authentication utility functions from auth.py
from .auth import (
    verify_password,
    get_password_hash,
    get_user_from_db,
    authenticate_user,
    create_access_token,
    placeholder_users_db,  # This is used for user registration
)

from backend.server.websocket_manager import WebSocketManager
from backend.server.server_utils import (
    get_config_dict,
    update_environment_variables, handle_file_upload, handle_file_deletion,
    execute_multi_agents, handle_websocket_communication
)


from gpt_researcher.utils.logging_config import setup_research_logging

import logging

# Get logger instance
logger = logging.getLogger(__name__)

# Don't override parent logger settings
logger.propagate = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Only log to console
    ]
)



# App initialization
app = FastAPI()

# Static files and templates
app.mount("/site", StaticFiles(directory="./frontend"), name="site")
app.mount("/static", StaticFiles(directory="./frontend/static"), name="static")
templates = Jinja2Templates(directory="./frontend")

# WebSocket manager
manager = WebSocketManager()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants and Directories
DOC_PATH = os.getenv("DOC_PATH", "./my-docs")
SECRET_KEY = "placeholder_secret_key"  # Replace with your actual secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Startup event


@app.on_event("startup")
def startup_event():
    os.makedirs("outputs", exist_ok=True)
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
    os.makedirs(DOC_PATH, exist_ok=True)
    

# Routes


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "report": None})


@app.get("/files/")
async def list_files():
    files = os.listdir(DOC_PATH)
    print(f"Files in {DOC_PATH}: {files}")
    return {"files": files}


@app.post("/api/multi_agents")
async def run_multi_agents():
    return await execute_multi_agents(manager)


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    return await handle_file_upload(file, DOC_PATH)


@app.delete("/files/{filename}")
async def delete_file(filename: str):
    return await handle_file_deletion(filename, DOC_PATH)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await handle_websocket_communication(websocket, manager)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# --- Authentication Routes ---

# Utility function to decode the JWT token from the cookie
def get_current_user_from_cookie(cookie_token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(cookie_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain user information",
            )
        return {"username": username}
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

@app.get("/me")
async def me(session: str = Cookie(None)):
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(session, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token does not contain user information")
        return {"username": username, "message": "User is logged in"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

@app.post("/register", response_model=User)
async def register(user: UserCreate):
    if user.username in placeholder_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    user_data = user.dict()
    user_data.pop("password")
    user_data.update({"hashed_password": hashed_password})
    placeholder_users_db[user.username] = user_data
    logger.info(f"Registered new user: {user.username}")
    return User(**user_data)

@app.post("/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    logger.info(f"User logged in: {user['username']}")

    response.set_cookie(
        key="session",
        value=access_token,
        httponly=True,  
        secure=True,  # CHANGE TO TRUE DURING PRODUCTION
        samesite="Lax",  
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        domain="localhost"
    )

    return {"message": "Login successful"}

@app.post("/logout")
def logout(response: Response):
    response.set_cookie(
        key="session",
        value="",
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=0  
    )
    return {"message": "Logout successful"}
