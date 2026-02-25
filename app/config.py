from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings

# Single source of truth for timezone — GMT+08
SGT = ZoneInfo("Asia/Singapore")


class Settings(BaseSettings):
    TOKEN: str
    WEBHOOK_URL: str
    WEBHOOK_SECRET: str
    SUPABASE_URL: str
    SUPABASE_SECRET_KEY: str
    SUPABASE_PUBLISHABLE_KEY: str
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env.local"
        extra = "ignore"


settings = Settings()
