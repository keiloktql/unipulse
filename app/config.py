from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TOKEN: str
    WEBHOOK_URL: str
    WEBHOOK_SECRET: str
    SUPABASE_URL: str
    SUPABASE_SECRET_KEY: str
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env.local"
        extra = "ignore"


settings = Settings()
