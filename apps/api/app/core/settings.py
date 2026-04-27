import os

from dotenv import load_dotenv

load_dotenv()


class SettingsError(RuntimeError):
    pass


class MissingRequiredEnvError(SettingsError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"{name} is not set")


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise MissingRequiredEnvError(name)

    return value


def get_cors_allow_origins() -> list[str]:
    raw_value = os.getenv("CORS_ALLOW_ORIGINS", "")

    if not raw_value.strip():
        return []

    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


def get_database_url() -> str:
    return get_required_env("DATABASE_URL")
