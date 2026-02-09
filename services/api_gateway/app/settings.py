from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# services/api_gateway (service root)
BASE_DIR = Path(__file__).resolve().parents[1]


ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    # --- DB ---
    DATABASE_URL: str

    # --- JWT ---
    # Optional, чтобы можно было запускать без JWT и не ломались Alembic/миграции.
    # Если None, то auth-функции будут явно падать с понятной ошибкой при попытке выпустить токен.
    JWT_SECRET_KEY: str | None = None

    # Алгоритм шифрования JWT-токена.
    JWT_ALGORITHM: str = "HS256"

    # Время жизни JWT-токена (в минутах).
    JWT_EXPIRES_MINUTES: int = 60


def load_settings() -> Settings:
    s = Settings()  # type: ignore[call-arg]
    # (опционально) явная проверка, чтобы упасть с понятной ошибкой, если env пустой
    if not s.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return s


settings = load_settings()
