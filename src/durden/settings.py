from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    name: str = "Durden Object Detection API"
    models: list[str] = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"]
    env: str = "production"
    version: str = "0.1.0"
    static_dir: Path = BASE_DIR / "static"

    preload_models: bool = False

    max_upload_bytes: int = 10 * 1024 * 1024
    max_image_pixels: int = 50_000_000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DURDEN_",
        extra="ignore",
    )


settings = Settings()
