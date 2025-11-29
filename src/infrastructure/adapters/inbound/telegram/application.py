import logging
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from .handlers import TelegramHandlers, UserStates, ReviewStates, DbControlStates


logger = logging.getLogger(__name__)

class Application:
    def __init__(self, telegram_handlers: TelegramHandlers, telegram_token: str):
        self._telegram_handlers = telegram_handlers
        self._application = ApplicationBuilder().token(telegram_token).build()

    def setup(self) -> None:
        regex_uuid = r"[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}"

        # --- User Flow Handlers ---
        start_handler = CommandHandler("start", self._telegram_handlers.start_command)
        cancel_handler = CommandHandler("cancel", self._telegram_handlers.cancel_command)

        # Forward Navigation
        purpose_router_handler = CallbackQueryHandler(self._telegram_handlers.purpose_router_callback, pattern=r"^(buy|sell|about)$")
        list_courses_handler = CallbackQueryHandler(self._telegram_handlers.list_courses_callback, pattern=r"^(buy|sell)$")
        list_subjects_handler = CallbackQueryHandler(self._telegram_handlers.list_subjects_callback, pattern=r"^course/\d+$")
        list_approved_notes_handler = CallbackQueryHandler(self._telegram_handlers.list_approved_notes_callback, pattern=fr"^subject/{regex_uuid}$")
        download_note_handler = CallbackQueryHandler(self._telegram_handlers.download_note_callback, pattern=fr"^note/{regex_uuid}$")
        prompt_upload_note_handler = CallbackQueryHandler(self._telegram_handlers.prompt_upload_note_callback, pattern=fr"^subject/{regex_uuid}$")

        upload_note_handler = MessageHandler(filters.Document.ALL, self._telegram_handlers.upload_note_handler)

        # Backward Navigation (The Back Buttons)
        back_to_start_handler = CallbackQueryHandler(self._telegram_handlers.back_to_start_callback, pattern=r"^back_to_start$")
        back_to_courses_handler = CallbackQueryHandler(self._telegram_handlers.back_to_courses_callback, pattern=r"^back_to_courses$")
        back_to_subjects_handler = CallbackQueryHandler(self._telegram_handlers.back_to_subjects_callback, pattern=r"^back_to_subjects$")

        user_conversation_handler = ConversationHandler(
            entry_points=[start_handler],
            states={
                UserStates.PURPOSE_ROUTER: [
                    purpose_router_handler,
                    back_to_start_handler
                ],
                UserStates.COURSE_SELECTION: [
                    list_courses_handler
                ],
                UserStates.SUBJECT_SELECTION: [
                    list_subjects_handler,
                    back_to_start_handler
                ],
                UserStates.NOTE_SELECTION: [
                    list_approved_notes_handler,
                    back_to_courses_handler
                ],
                UserStates.NOTE_DOWNLOAD: [
                    download_note_handler,
                    back_to_subjects_handler
                ],
                UserStates.NOTE_UPLOAD_PROMPT: [
                    prompt_upload_note_handler,
                    back_to_courses_handler
                ],
                UserStates.NOTE_UPLOAD: [
                    upload_note_handler,
                    back_to_subjects_handler
                ],
            },
            fallbacks=[cancel_handler],
            per_user=True,
            per_chat=False,
            allow_reentry=True,
        )

        self._application.add_handler(user_conversation_handler)
        logger.debug("User conversation handler added")

        # --- Review Flow Handlers ---
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
        logger.debug("Review conversation handler added")

        # --- Admin DB Handlers ---
        add_subject_handler = CommandHandler("add", self._telegram_handlers.add_subject_command)

        # Forward Navigation for Admin DB Handlers
        subject_prompt_handler = CallbackQueryHandler(self._telegram_handlers.subject_prompt_callback, pattern=r"^course/\d+$")
        subject_addition_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, self._telegram_handlers.subject_addition_callback)
        subject_addition_confirmation_handler = CallbackQueryHandler(self._telegram_handlers.subject_addition_confirmation_callback, pattern=fr"^confirm_add_subject/.*$")

        # Backward Navigation for Admin DB Handlers
        back_to_courses_from_db_handler = CallbackQueryHandler(self._telegram_handlers.back_to_courses_from_db_callback, pattern=r"^back_to_courses$")

        db_conversation_handler = ConversationHandler(
            entry_points=[add_subject_handler],
            states={
                DbControlStates.SUBJECT_PROMPT: [
                    subject_prompt_handler,
                ],
                DbControlStates.SUBJECT_ADDITION: [
                    subject_addition_handler,
                ],
                DbControlStates.SUBJECT_ADDITION_CONFIRMATION: [
                    subject_addition_confirmation_handler,
                    back_to_courses_from_db_handler
                ],
                DbControlStates.REPEAT_ADD_SUBJECT_CHECK: [
                    subject_prompt_handler,
                    back_to_courses_from_db_handler,
                ]
            },
            fallbacks=[cancel_handler],
            per_user=True,
            per_chat=False,
            allow_reentry=True,
        )

        self._application.add_handler(db_conversation_handler)
        logger.debug("DB administration conversation handler added")

    def run(self) -> None:
        self._application.run_polling()