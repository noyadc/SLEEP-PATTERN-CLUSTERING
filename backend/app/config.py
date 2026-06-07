from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://sleepuser:sleeppass@localhost:5432/sleep_analytics"
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:3000"
    upload_dir: str = "uploads"

    class Config:
        env_file = ".env"


settings = Settings()
