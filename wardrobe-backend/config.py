from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    gemini_api_key: str
    # Override in .env to switch models, e.g. when this one is overloaded or retired.
    gemini_model: str = "gemini-3.6-flash"

    class Config:
        env_file = ".env"

settings = Settings()