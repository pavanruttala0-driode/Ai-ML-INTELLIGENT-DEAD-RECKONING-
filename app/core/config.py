from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SIH26168 Dead Reckoning Backend"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/deadreckoning"
    gnss_timeout_seconds: float = 3.0

    class Config:
        env_file = ".env"


settings = Settings()
