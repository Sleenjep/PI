from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = "SUPER_SECRET_KEY"
    algorithm: str = "HS256"
    oauth2_token_url: str = "http://localhost:8001/login"

    class Config:
        env_file = ".env"


settings = Settings()
