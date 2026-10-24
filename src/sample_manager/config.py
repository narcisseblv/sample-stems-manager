from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)

class Settings(BaseSettings):
    database_url: str = "sqlite:///./samples.db"
    upload_dir: Path = Path("uploads")
    max_audio_size_bytes: int = 50 * 1024 * 1024


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
