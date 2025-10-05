from src.core.domain.common.enums import StartActions


class StartInteractionService:
    def __init__(self, welcome_message: str):
        self._welcome_message = welcome_message

    def get_start_data(self):
        actions = list(StartActions)

        return {
            "message": self._welcome_message,
            "actions": actions
        }