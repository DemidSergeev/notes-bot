from pydantic_settings import BaseSettings
from pydantic import (
    computed_field,
    PostgresDsn,
)
import json
import pathlib
from typing import Any


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

    TELEGRAM_ADMIN_ID: int

    @computed_field
    @property
    def TELEGRAM_WELCOME_MESSAGE(self) -> str:
        welcome_message_file_path = pathlib.Path(__file__).parent.parent.parent / "assets" / "welcome.txt"
        if welcome_message_file_path.exists():
            with open(welcome_message_file_path) as f:
                return f.read()
        return "Welcome to the Notes Bot!"

    PAYMENT_DETAILS: str

    LOGGER_NAME: str = "notes_bot"
    LOGGER_LOGFILE_NAME: str = "notes_bot.log"

    @computed_field
    @property
    def LOGGING_CONFIG(self) -> dict[str, Any]:
        """This property depends on presence and structure of logging_config.json"""
        config_file_path = pathlib.Path(__file__).parent.parent.parent / "config" / "logging_config.json"
        with open(config_file_path) as f:
            config = json.load(f)
            config["handlers"]["file"]["filename"] = self.LOGGER_LOGFILE_NAME
            return config


settings = Settings()