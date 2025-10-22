from enum import Enum
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, CallbackQueryHandler

from .handlers import TelegramHandlers, States


class Application:
    def __init__(self, telegram_handlers: TelegramHandlers, telegram_token: str):
        self._telegram_handlers = telegram_handlers
        self._application = ApplicationBuilder().token(telegram_token).build()

    def setup(self) -> None:
        regex_uuid = r"[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}"

        start_handler = CommandHandler("start", self._telegram_handlers.start_command)
        cancel_handler = CommandHandler("cancel", self._telegram_handlers.cancel_command)
        list_courses_handler = CallbackQueryHandler(self._telegram_handlers.list_courses_callback, pattern=r"^(buy|sell)$")
        list_subjects_handler = CallbackQueryHandler(self._telegram_handlers.list_subjects_callback, pattern=r"^(buy|sell)/course/\d+$")
        list_notes_handler = CallbackQueryHandler(self._telegram_handlers.list_notes_callback, pattern=r"^buy/subject/" + regex_uuid + r"$")
        buy_note_handler = CallbackQueryHandler(self._telegram_handlers.buy_note_callback, pattern=r"^buy/note/" + regex_uuid + r"$")

        conversation_handler = ConversationHandler(
            entry_points=[start_handler],
            states={
                States.COURSE_SELECTION: [list_courses_handler],
                States.SUBJECT_SELECTION: [list_subjects_handler],
                States.NOTE_SELECTION: [list_notes_handler],
                States.PURCHASE_CONFIRMATION: [buy_note_handler],
            },
            fallbacks=[cancel_handler],
            per_user=True,
            per_chat=False,
        )

        self._application.add_handler(conversation_handler)

    def run(self) -> None:
        self._application.run_polling()
