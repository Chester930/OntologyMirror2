from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "OntologyMirror"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    GOOGLE_API_KEY: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    
    DEFAULT_LLM_MODEL: str = "gpt-4-turbo" # or gemini-pro

    # Schema.org Config
    SCHEMA_ORG_VERSION: str = "27.0"
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
