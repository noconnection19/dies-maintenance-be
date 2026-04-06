from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Dies Maintenance API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database — ganti ke PostgreSQL kalau sudah siap:
    # DATABASE_URL: str = "postgresql://user:pass@localhost/dies_db"
    DATABASE_URL: str = "sqlite:///./dies_maintenance.db"

    # CORS origins yang diizinkan (Flutter Web dev server)
    CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
