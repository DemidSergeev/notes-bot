import random
import logging
import io
import uuid
import html
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from src.core.application.ports.inbound import DataServicePort, PurchaseServicePort, SellServicePort, ReviewServicePort
from src.core.domain.models import User
from src.core.domain.common.enums import StartActions, CourseYear


logger = logging.getLogger(__name__)

class UserStates(Enum):
    END = ConversationHandler.END
    COURSE_SELECTION = 1
    SUBJECT_SELECTION = 2
    NOTE_SELECTION = 3
    PURCHASE_CONFIRMATION = 4
    NOTE_UPLOAD_PROMPT = 5
    NOTE_UPLOAD = 6

class ReviewStates(Enum):
    END = ConversationHandler.END
    NOTE_REVIEW = 1
    NOTE_DECISION = 2

class TelegramHandlers:
    def __init__(
        self,
        data_service: DataServicePort,
        purchase_service: PurchaseServicePort,
        sell_service: SellServicePort,
        review_service: ReviewServicePort,
        welcome_message: str,
        admin_ids: list[int],
        ) -> None:
        self._data_service = data_service
        self._purchase_service = purchase_service
        self._sell_service = sell_service
        self._review_service = review_service
        self._welcome_message = welcome_message
        self._admin_ids = admin_ids

    # --- HELPER METHODS FOR RENDERING MENUS ---

    async def _render_start_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_edit: bool = False):
        buttons = [
            InlineKeyboardButton(text=action.value.label, callback_data=action.value.code)
            for action in list(StartActions)
        ]
        keyboard = InlineKeyboardMarkup([buttons])

        if is_edit and update.callback_query:
            await update.callback_query.message.edit_text(self._welcome_message, reply_markup=keyboard)
        else:
            await update.message.reply_text(self._welcome_message, reply_markup=keyboard)

    async def _render_courses_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        courses = self._data_service.get_courses()
        reply = "Выберите курс:\n"

        # Create buttons for courses
        buttons = []
        for course in courses:
            buttons.append([InlineKeyboardButton(text=f"Курс {course.year.value}", callback_data=f"course/{course.year.value}")])
        
        # Add Back button
        buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back_to_start")])

        await update.callback_query.message.edit_text(
            reply if courses else "Курсы ещё не добавили :(", 
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def _render_subjects_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        course_year = context.user_data.get("course_year")
        if not course_year:
            # Fallback if state is lost, though strictly shouldn't happen in normal flow
            await self._render_courses_menu(update, context)
            return

        subjects = self._data_service.get_subjects(course_year)
        reply = f"Выберите предмет ({course_year.value}-й курс):\n"

        buttons = []
        for subject in subjects:
            buttons.append([InlineKeyboardButton(text=subject.name, callback_data=f"subject/{subject.id}")])

        # Add Back button
        buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back_to_courses")])

        await update.callback_query.message.edit_text(
            reply if subjects else "Предметы по этому курсу ещё не добавили :(", 
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # --- START & CANCEL HANDLERS ---

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        context.user_data.clear()
        await self._render_start_menu(update, context, is_edit=False)
        return UserStates.COURSE_SELECTION

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Состояние сброшено. Начинаю заново.")
        context.user_data.clear()
        await self._render_start_menu(update, context, is_edit=False)
        return UserStates.COURSE_SELECTION

    # --- BACK NAVIGATION HANDLERS ---

    async def back_to_start_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        context.user_data.pop("purpose", None)
        await self._render_start_menu(update, context, is_edit=True)
        return UserStates.COURSE_SELECTION

    async def back_to_courses_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        context.user_data.pop("course_year", None)
        await self._render_courses_menu(update, context)
        return UserStates.SUBJECT_SELECTION

    async def back_to_subjects_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        context.user_data.pop("subject_id", None)
        
        # Render the menu
        await self._render_subjects_menu(update, context)

        # Return the correct state based on original purpose
        purpose = context.user_data.get("purpose")
        match purpose:
            case "buy":
                return UserStates.NOTE_SELECTION
            case "sell":
                return UserStates.NOTE_UPLOAD_PROMPT
            case _:
                # Fallback
                return UserStates.SUBJECT_SELECTION

    # --- MAIN FLOW HANDLERS ---

    async def list_courses_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        purpose = query.data
        if purpose not in [action.value.code for action in [StartActions.BUY, StartActions.SELL]]:
            return

        context.user_data["purpose"] = purpose
        logger.debug("User %s (ID %s) selecting courses for purpose '%s'", update.effective_user.full_name, update.effective_user.id, purpose)

        await self._render_courses_menu(update, context)
        return UserStates.SUBJECT_SELECTION

    async def list_subjects_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 2 or data_parts[0] != "course":
            return

        course_year = CourseYear(int(data_parts[1]))
        context.user_data["course_year"] = course_year

        await self._render_subjects_menu(update, context)

        purpose = context.user_data["purpose"]
        match purpose:
            case "buy":
                return UserStates.NOTE_SELECTION
            case "sell":
                return UserStates.NOTE_UPLOAD_PROMPT

    async def list_approved_notes_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 2 or data_parts[0] != "subject":
            return

        subject_id = data_parts[1]
        context.user_data["subject_id"] = uuid.UUID(subject_id)

        notes = self._data_service.get_approved_notes_by_subject_id(subject_id)
        reply = "Выберите конспект:\n"

        buttons = []
        for note in notes:
            buttons.append([InlineKeyboardButton(text=note.title, callback_data=f"note/{note.id}")])
        
        # Add Back button
        buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back_to_subjects")])

        await query.message.edit_text(reply if len(buttons) > 1 else "Конспекты по этому предмету ещё не добавили :(", reply_markup=InlineKeyboardMarkup(buttons))

        return UserStates.PURCHASE_CONFIRMATION

    async def buy_note_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 2 or data_parts[0] != "note":
            return

        note_id = data_parts[1]
        context.user_data["note_id"] = uuid.UUID(note_id)

        user = update.effective_user
        buyer = User(external_id=user.id, name=user.full_name)

        receipt = self._purchase_service.generate_purchase_receipt(note_id=note_id, buyer=buyer)

        # Here we provide a button to go back to the note list if they change their mind, 
        # or we could end the conversation. 
        buttons = [[InlineKeyboardButton(text="« Вернуться к списку", callback_data="back_to_subjects")]]

        await query.message.edit_text(
            f"Создана заявка на покупку конспекта.\nРеквизиты для оплаты конспекта: {receipt.payment_details}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        # We stay in PURCHASE_CONFIRMATION to allow the back button to work
        return UserStates.PURCHASE_CONFIRMATION 

    async def prompt_upload_note_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 2 or data_parts[0] != "subject":
            return
        
        subject_id = data_parts[1]
        context.user_data["subject_id"] = subject_id

        reply = "Загрузите файл конспекта."
        buttons = [[InlineKeyboardButton(text="« Назад", callback_data="back_to_subjects")]]

        await query.message.edit_text(reply, reply_markup=InlineKeyboardMarkup(buttons))
        return UserStates.NOTE_UPLOAD

    async def upload_note_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        document = update.message.document
        if not document:
            await update.message.reply_text("Пожалуйста, отправьте конспект в виде файла (документа).")
            return UserStates.NOTE_UPLOAD

        subject_id = context.user_data.get("subject_id")
        
        try:
            bot = context.bot
            file_handler = await bot.get_file(document.file_id)
            file = io.BytesIO()
            await file_handler.download_to_memory(file)
            self._sell_service.upload_note(
                title=document.file_name,
                price_rub=random.randint(50, 300),
                subject_id=subject_id,
                file=file,
            )
            
            await update.message.reply_text(
                f'Спасибо, файл "{document.file_name}" отправлен на модерацию! Мы свяжемся с вами после проверки.'
            )
            
            # Reset workflow
            context.user_data.clear()
            await self._render_start_menu(update, context, is_edit=False)
            return UserStates.COURSE_SELECTION

        except Exception:
            logger.exception("Error uploading note")
            await update.message.reply_text("Произошла ошибка при загрузке. Попробуйте ещё раз.")
            return UserStates.NOTE_UPLOAD

    # --- REVIEW HANDLERS ---

    async def start_review_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user.id not in self._admin_ids:
            await update.message.reply_text("У вас нет прав для этой команды.")
            return ConversationHandler.END

        not_approved_notes = self._data_service.get_not_approved_notes()

        if not not_approved_notes:
            await update.message.reply_text("Нет конспектов на модерацию.")
            return ConversationHandler.END

        notes_to_review = list(set.union(
            set(note for note in not_approved_notes),
            context.user_data.get("notes_to_review", set())
        ))
        context.user_data["notes_to_review"] = notes_to_review
        context.user_data["notes_to_review_index"] = 0
        
        buttons = [
            InlineKeyboardButton(text="Начать модерацию", callback_data=f"review/{notes_to_review[0].id}")
        ]

        await update.message.reply_text(f"Конспекты на модерацию: {len(not_approved_notes)}\n", reply_markup=InlineKeyboardMarkup([buttons]))

        return ReviewStates.NOTE_REVIEW

    async def review_note_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 2 or data_parts[0] != "review":
            return

        note_id = data_parts[1]
        
        # Safe access to notes list
        notes = context.user_data.get("notes_to_review", [])
        index = context.user_data.get("notes_to_review_index", 0)
        
        if not notes or index >= len(notes):
             await query.message.edit_text("Список конспектов устарел или пуст.")
             return ReviewStates.END

        note_title = html.escape(notes[index].title)
        note_url = self._data_service.get_note_url(note_id)

        if not note_url:
            await query.message.edit_text("Ошибка при получении конспекта для модерации.")
            return ReviewStates.END

        await query.message.edit_text(f'Конспект для модерации: <a href="{note_url}">{note_title}</a>', parse_mode=ParseMode.HTML)

        buttons = [
            InlineKeyboardButton(text="Одобрить", callback_data=f"approve/{note_id}"),
            InlineKeyboardButton(text="Отклонить", callback_data=f"reject/{note_id}")
        ]

        await query.message.reply_text("Просмотрите конспект и выберите действие:", reply_markup=InlineKeyboardMarkup([buttons]))

        return ReviewStates.NOTE_DECISION

    async def approve_note_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 2 or data_parts[0] != "approve":
            return

        note_id = data_parts[1]
        self._review_service.approve_note(note_id)

        await query.message.edit_text("Конспект одобрен и опубликован.")
        return ReviewStates.END

    async def reject_note_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 2 or data_parts[0] != "reject":
            return

        note_id = data_parts[1]
        # In a real scenario, you might want to get the reason from the moderator
        reason = "Не соответствует требованиям."
        # Assuming we can find the owner via the note ID in the service, or passing None if not required immediately
        self._review_service.reject_note(note_id=note_id, reason=reason)

        await query.message.edit_text("Конспект отклонён и удалён.")
        return ReviewStates.END