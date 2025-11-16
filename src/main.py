from src.infrastructure.config.wiring import application
from src.infrastructure.config.database import init_database
from src.infrastructure.config.storage import create_bucket
from src.infrastructure.config.logger import setup_logging

if __name__ == "__main__":
    setup_logging()
    init_database()
    create_bucket()
    application.setup()
    application.run()