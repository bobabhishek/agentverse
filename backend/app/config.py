import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    # App config
    APP_NAME: str = "A2A Guard Backend"
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # Agent 2 config
    AGENT2_NAME: str = "agent-2-india"
    AGENT2_REGION: str = "south-india"
    AGENT2_MODEL: str = "gpt-4o"
    AGENT2_OPENAI_API_KEY: str = ""
    AGENT2_AZURE_ENDPOINT: str = ""
    AGENT2_AZURE_API_KEY: str = ""
    AGENT2_AZURE_DEPLOYMENT: str = ""
    AGENT2_AZURE_API_VERSION: str = ""

    # Agent 1 config
    AGENT1_NAME: str = "agent-1-europe"
    AGENT1_REGION: str = "north-europe"
    AGENT1_MODEL: str = "gpt-5.4-mini"
    AGENT1_OPENAI_API_KEY: str = ""
    AGENT1_AZURE_ENDPOINT: str = ""
    AGENT1_AZURE_API_KEY: str = ""
    AGENT1_AZURE_DEPLOYMENT: str = "gpt-5.4-mini"
    AGENT1_AZURE_API_VERSION: str = ""

    # Azure OpenAI / Azure API Shared Settings
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"

    # Data config
    SYNTHETIC_DATA_PATH: str = "app/data/synthetic_customers.json"

    # Test config
    TEST_DATA_MINIMIZATION_VIOLATION: bool = False
    ENABLE_SYNTHETIC_DATA_ONLY: bool = True
    GDPR_VIOLATION_PROBABILITY: float = 0.75

    # Logging config
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else ".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

