from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings

# MongoDB settings class
class MongoDBSettings(BaseSettings):
    MONGO_URI: str
    MONGO_DB_NAME: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"
        extra = "ignore"

# Load settings from the environment
mongodb_settings = MongoDBSettings()

# Initialize the MongoDB client and database
client = AsyncIOMotorClient(mongodb_settings.MONGO_URI)
db = client[mongodb_settings.MONGO_DB_NAME]

# Function to verify the connection to MongoDB
async def verify_mongodb_connection():
    try:
        await client.admin.command("ping")
        print("[CONNECTION SUCCESS] MongoDB connected successfully.")
    except Exception as e:
        print(f"[CONNECTION FAILURE] Failed to connect to MongoDB: {e}")
        raise

__all__ = ["db", "mongodb_settings", "verify_mongodb_connection"]
