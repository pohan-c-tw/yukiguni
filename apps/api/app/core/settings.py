import os

from dotenv import load_dotenv

load_dotenv()


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"{name} is not set")

    return value


def get_database_url() -> str:
    return get_required_env("DATABASE_URL")


def get_cors_allow_origins() -> list[str]:
    raw_value = os.getenv("CORS_ALLOW_ORIGINS", "")

    if not raw_value.strip():
        return []

    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]
