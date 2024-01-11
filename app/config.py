from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Environment variables
    adobe_client_id: str
    adobe_client_secret: str
    openai_api_key: str

    # Custom values
    extract_dir_path: Path = "data/interim/000-adobe-extract"
    data_path: Path
    openai_timeout: int = 30
    """Timeout in seconds for OpenAI API calls"""
    openai_model_temperature: int = 0.0
    """Temperature for OpenAI API calls"""
