import os
from datetime import timedelta

import jwt

from fastapi import (
    FastAPI,
    Request,
    WebSocket,
    WebSocketDisconnect,
    File,
    UploadFile,
    Header,
    HTTPException,
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
    User,
    UserCreate,
)

from .auth import (
    authenticate_user, 
    create_access_token, 
    register_user
)
from .mongodb_config import (
    verify_mongodb_connection,
    mongodb_settings
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
    allow_origins=[os.getenv('REACT_APP_URL')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants and Directories
DOC_PATH = os.getenv("DOC_PATH", "./my-docs")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Startup event


@app.on_event("startup")
async def startup_event():
    os.makedirs("outputs", exist_ok=True)
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
    os.makedirs(DOC_PATH, exist_ok=True)
    await verify_mongodb_connection()
    

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

@app.post("/register", response_model=User)
async def register(user: UserCreate):
    try:
        return await register_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    
    response.set_cookie(
        key="session",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        domain=os.getenv("APP_DOMAIN")
    )

    return {"message": "Login successful"}




@app.get("/me")
async def me(session: str = Cookie(None)):
    """
    Endpoint to retrieve information about the currently authenticated user.
    """
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(session, mongodb_settings.SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "message": "User is logged in"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/logout")
def logout(response: Response):
    """
    Logout endpoint that clears the session cookie.
    """
    response.set_cookie(
        key="session",
        value="",
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=0,
        domain=os.getenv("APP_DOMAIN")
    )
    return {"message": "Logout successful"}