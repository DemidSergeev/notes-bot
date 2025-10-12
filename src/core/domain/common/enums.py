from enum import Enum, StrEnum


class CourseYear(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6


class StartActions(StrEnum):
    BUY = "Купить",
    SELL = "Продать",
    ABOUT = "О нас"