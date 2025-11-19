from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "task_3_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DIAGNOSTICS_DIR = OUTPUT_DIR / "_diagnostics"
DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    google_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.0
    gemini_max_output_tokens: int = 8192  # Increased for longer responses
    max_report_chars: int = 15000  # Increased to capture more details from reports

    class Config:
        env_file = ROOT_DIR / ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
