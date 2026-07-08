from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    name: str
    models: list[str]
    env: str
    version: str
    static_dir: Path

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
