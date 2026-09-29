import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "FEMA Agent Guardrail Backend"
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # Azure AI Foundry / Microsoft Foundry configuration
    FOUNDRY_ENDPOINT: str = ""
    FOUNDRY_API_KEY: str = ""
    FOUNDRY_MODEL: str = "gpt-4o"
    FOUNDRY_REGION: str = "south-india"
    FOUNDRY_RESOURCE: str = "projgdpr1"

    # WireMock Simulated Wire Transfer Sandbox
    WIREMOCK_BASE_URL: str = ""

    # Synthetic Dataset Path
    DATA_PATH: str = str(Path(__file__).resolve().parent / "data" / "fema_synthetic_100_people.json")

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
