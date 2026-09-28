import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env from backend directory or project root
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_file_path = os.path.join(backend_dir, "..", ".env")
if not os.path.exists(env_file_path):
    env_file_path = os.path.join(backend_dir, "..", "backend", ".env")

load_dotenv(os.path.abspath(env_file_path))

class Settings(BaseSettings):
    PROJECT_NAME: str = "NICE HackArena KYC & AML Checker"
    API_V1_STR: str = "/api"
    
    # Reads DATABASE_URL from environment or fallback
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./kyc_aml.db"
    )
    
    # Matching thresholds
    FUZZY_HIGH_THRESHOLD: float = 90.0
    FUZZY_MEDIUM_THRESHOLD: float = 75.0

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
