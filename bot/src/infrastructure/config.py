from pydantic_settings import BaseSettings
from pydantic import (
    computed_field,
    PostgresDsn,
)


class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @computed_field
    @property
    def POSTGRES_DSN(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg3",
            user=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB
        )

settings = Settings()