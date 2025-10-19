from src.infrastructure.config.wiring import course_commands
from src.infrastructure.config.database import init_database

if __name__ == "__main__":
    init_database()
    course_commands.list_courses()