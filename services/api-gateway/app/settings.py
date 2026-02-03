from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# services/api-gateway (service root)
BASE_DIR = Path(__file__).resolve().parents[1]


ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    DATABASE_URL: str


settings = Settings()
