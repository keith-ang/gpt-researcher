from pydantic import BaseModel, EmailStr
from typing import Optional

# --- Existing Models ---

class ResearchRequest(BaseModel):
    task: str
    report_type: str
    agent: str

class ConfigRequest(BaseModel):
    ANTHROPIC_API_KEY: str
    TAVILY_API_KEY: str
    LANGCHAIN_TRACING_V2: str
    LANGCHAIN_API_KEY: str
    OPENAI_API_KEY: str
    DOC_PATH: str
    RETRIEVER: str
    GOOGLE_API_KEY: str = ''
    GOOGLE_CX_KEY: str = ''
    BING_API_KEY: str = ''
    SEARCHAPI_API_KEY: str = ''
    SERPAPI_API_KEY: str = ''
    SERPER_API_KEY: str = ''
    SEARX_URL: str = ''
    XAI_API_KEY: str
    DEEPSEEK_API_KEY: str

# --- Updated Authentication Models ---

# Base information common to all user representations.
class UserBase(BaseModel):
    username: str
    email: EmailStr
    organisation_name: str

# Model used when creating a new user (includes the raw password).
class UserCreate(UserBase):
    password: str
    confirm_password: str

# Model stored in the "database" (password stored as a hash).
class UserInDB(UserBase):
    hashed_password: str

# Model returned to clients (does not include any password information).
class User(UserBase):
    pass

