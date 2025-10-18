from src.infrastructure.config.wiring import course_commands
from src.infrastructure.config.database import create_db_and_tables

if __name__ == "__main__":
    create_db_and_tables()
    course_commands.list_courses()