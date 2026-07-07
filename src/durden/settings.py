from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    name: str
    models: list[str]
    env: str
    version: str
    static_dir: Path

    class Config:
        env_file = ".env"

settings = Settings()