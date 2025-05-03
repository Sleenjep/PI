from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # JWT
    secret_key: str = Field("SUPER_SECRET_KEY", env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")

    # PostgreSQL
    db_host: str = Field("localhost", env="POSTGRES_HOST")
    db_port: int = Field(5432, env="POSTGRES_PORT")
    db_user: str = Field("myuser", env="POSTGRES_USER")
    db_password: str = Field("mypassword", env="POSTGRES_PASSWORD")
    db_name: str = Field("users_db", env="POSTGRES_DB")

    # Redis
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_ttl: int = Field(300, env="REDIS_TTL")

    class Config:
        env_file = ".env"


settings = Settings()
