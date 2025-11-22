import logging
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from .handlers import TelegramHandlers, UserStates, ReviewStates


logger = logging.getLogger(__name__)

class Application:
    def __init__(self, telegram_handlers: TelegramHandlers, telegram_token: str):
        self._telegram_handlers = telegram_handlers
        self._application = ApplicationBuilder().token(telegram_token).build()

    def setup(self) -> None:
        regex_uuid = r"[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}"

        # User commands
        start_handler = CommandHandler("start", self._telegram_handlers.start_command)
        cancel_handler = CommandHandler("cancel", self._telegram_handlers.cancel_command)

        list_courses_handler = CallbackQueryHandler(self._telegram_handlers.list_courses_callback, pattern=r"^(buy|sell)$")
        list_subjects_handler = CallbackQueryHandler(self._telegram_handlers.list_subjects_callback, pattern=r"^course/\d+$")
        list_notes_handler = CallbackQueryHandler(self._telegram_handlers.list_notes_callback, pattern=fr"^subject/{regex_uuid}$")
        buy_note_handler = CallbackQueryHandler(self._telegram_handlers.buy_note_callback, pattern=fr"^note/{regex_uuid}$")
        prompt_upload_note_handler = CallbackQueryHandler(self._telegram_handlers.prompt_upload_note_callback, pattern=fr"^subject/{regex_uuid}$")

        upload_note_handler = MessageHandler(filters.Document.ALL, self._telegram_handlers.upload_note_handler)

        user_conversation_handler = ConversationHandler(
            entry_points=[start_handler],
            states={
                UserStates.COURSE_SELECTION: [list_courses_handler],
                UserStates.SUBJECT_SELECTION: [list_subjects_handler],
                UserStates.NOTE_SELECTION: [list_notes_handler],
                UserStates.PURCHASE_CONFIRMATION: [buy_note_handler],
                UserStates.NOTE_UPLOAD_PROMPT: [prompt_upload_note_handler],
                UserStates.NOTE_UPLOAD: [upload_note_handler],
            },
            fallbacks=[cancel_handler],
            per_user=True,
            per_chat=False,
            allow_reentry=True,
        )

        self._application.add_handler(user_conversation_handler)
        logger.debug("Conversation handler added")

        # Review commands
        start_review_handler = CommandHandler("review", self._telegram_handlers.start_review_command)

        review_note_handler = CallbackQueryHandler(self._telegram_handlers.review_note_callback, pattern=fr"^review/{regex_uuid}$")
        approve_note_handler = CallbackQueryHandler(self._telegram_handlers.approve_note_callback, pattern=fr"^approve/{regex_uuid}$")
        reject_note_handler = CallbackQueryHandler(self._telegram_handlers.reject_note_callback, pattern=fr"^reject/{regex_uuid}$")

        review_conversation_handler = ConversationHandler(
            entry_points=[start_review_handler],
            states={
                ReviewStates.NOTE_REVIEW: [review_note_handler],
                ReviewStates.NOTE_DECISION: [approve_note_handler, reject_note_handler],
            },
            fallbacks=[cancel_handler],
            per_user=True,
            per_chat=False,
            allow_reentry=True,
        )
        self._application.add_handler(review_conversation_handler)
        logger.debug("Review handler added")

    def run(self) -> None:
        self._application.run_polling()
