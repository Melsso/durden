from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    name: str
    models: list[str]
    env: str
    version: str
    static_dir: Path = BASE_DIR / "static"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
