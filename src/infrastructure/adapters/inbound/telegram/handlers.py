import random
import logging
import io
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.core.application.ports.inbound import PurchaseServicePort, DataServicePort, SellServicePort
from src.core.domain.models import User
from src.core.domain.common.enums import StartActions, CourseYear


logger = logging.getLogger(__name__)

class States(Enum):
    START = 1
    COURSE_SELECTION = 2
    SUBJECT_SELECTION = 3
    NOTE_SELECTION = 4
    PURCHASE_CONFIRMATION = 5
    NOTE_UPLOAD_PROMPT = 6
    NOTE_UPLOAD = 7

class TelegramHandlers:
    def __init__(
        self,
        purchase_service: PurchaseServicePort,
        data_service: DataServicePort,
        sell_service: SellServicePort,
        welcome_message: str
        ) -> None:
        self._purchase_service = purchase_service
        self._data_service = data_service
        self._sell_service = sell_service
        self._welcome_message = welcome_message

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        buttons = [
            InlineKeyboardButton(text=action.value.label, callback_data=action.value.code)
            for action in list(StartActions)
        ]
        await update.message.reply_text(self._welcome_message, reply_markup=InlineKeyboardMarkup([buttons]))
        return States.COURSE_SELECTION

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Операция отменена.")
        context.user_data.clear()

    async def list_courses_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        if query.data not in ["buy", "sell"]:
            return

        courses = self._data_service.get_courses()
        reply = "Выберите курс:\n"
        buttons = [
            InlineKeyboardButton(text=f"Курс {course.year.value}", callback_data=f"{query.data}/course/{course.year.value}")
            for course in courses
        ]
        await query.message.reply_text(reply if buttons else "Курсы ещё не добавили :(", reply_markup=InlineKeyboardMarkup([buttons]))
        return States.SUBJECT_SELECTION

    async def list_subjects_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 3 or data_parts[0] not in ["buy", "sell"] or data_parts[1] != "course":
            return

        purpose = data_parts[0]
        course_year = CourseYear(int(data_parts[2]))
        subjects = self._data_service.get_subjects(course_year)
        reply = f"Выберите предмет ({course_year.value}-й курс):\n"

        buttons = [
            InlineKeyboardButton(text=subject.name, callback_data=f"{data_parts[0]}/subject/{subject.id}")
            for subject in subjects
        ]
        await query.message.reply_text(reply if buttons else "Предметы по этому курсу ещё не добавили :(", reply_markup=InlineKeyboardMarkup([buttons]))

        match purpose:
            case "buy":
                return States.NOTE_SELECTION
            case "sell":
                return States.NOTE_UPLOAD_PROMPT

    async def list_notes_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 3 or data_parts[0] != "buy" or data_parts[1] != "subject":
            return

        subject_id = data_parts[2]
        notes = self._data_service.get_notes(subject_id)
        reply = "Выберите конспект:\n"

        buttons = [
            InlineKeyboardButton(text=note.title, callback_data=f"{data_parts[0]}/note/{note.id}")
            for note in notes
        ]
        await query.message.reply_text(reply if buttons else "Конспекты по этому предмету ещё не добавили :(", reply_markup=InlineKeyboardMarkup([buttons]))
        return States.PURCHASE_CONFIRMATION

    async def buy_note_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 3 or data_parts[0] != "buy" or data_parts[1] != "note":
            return

        note_id = data_parts[2]
        user = update.effective_user
        buyer = User(external_id=user.id, name=user.full_name)

        receipt = self._purchase_service.generate_purchase_receipt(note_id=note_id, buyer=buyer)
        print("Notify admin (stub):", receipt)
        await query.message.reply_text(f"Реквизиты для оплаты конспекта: {receipt.payment_details}")

    async def prompt_upload_note_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 3 or data_parts[0] != "sell" or data_parts[1] != "subject":
            return
        
        subject_id = data_parts[2]
        reply = "Загрузите файл конспекта."

        context.user_data["subject_id"] = subject_id

        await query.message.reply_text(reply)
        return States.NOTE_UPLOAD

    async def upload_note_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        document = update.message.document
        if not document:
            await update.message.reply_text("Пожалуйста, отправьте конспект в виде файла (документа).")
            return States.NOTE_UPLOAD

        subject_id = context.user_data.get("subject_id")
        # user = update.effective_user
        # seller = User(external_id=user.id, name=user.full_name)
        
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
                f"Спасибо, файл {document.file_name} отправлен на модерацию! Мы свяжемся с вами после проверки."
            )
            context.user_data.clear()
            return States.START

        except Exception:
            # Handle potential errors during service call (e.g., storage failure)
            logger.exception("Error uploading note")
            await update.message.reply_text("Произошла ошибка при загрузке. Попробуйте ещё раз.")
            return States.NOTE_UPLOAD