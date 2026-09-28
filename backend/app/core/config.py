import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Explicitly load .env file from project root or backend folder
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

class Settings(BaseSettings):
    PROJECT_NAME: str = "NICE HackArena KYC & AML Checker"
    API_V1_STR: str = "/api"
    
    # Reads DATABASE_URL from .env file directly
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
