from enum import Enum


class CourseYear(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6

class ActionPair:
    def __init__(self, label: str, code: str) -> None:
        self.label = label
        self.code = code

class StartActions(Enum):
    BUY = ActionPair("Купить", "buy")
    SELL = ActionPair("Продать", "sell")
    ABOUT = ActionPair("О нас", "about")