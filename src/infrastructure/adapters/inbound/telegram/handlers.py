from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.core.application.ports.inbound import PurchaseServicePort
from src.core.domain.models import Buyer
from src.core.domain.common.enums import StartActions, CourseYear


class States(Enum):
    START = 1
    COURSE_SELECTION = 2
    SUBJECT_SELECTION = 3
    NOTE_SELECTION = 4
    PURCHASE_CONFIRMATION = 5

class TelegramHandlers:
    def __init__(self, purchase_service: PurchaseServicePort, welcome_message: str) -> None:
        self._purchase_service = purchase_service
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

        courses = self._purchase_service.get_courses()
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

        course_year = CourseYear(int(data_parts[2]))
        subjects = self._purchase_service.get_subjects(course_year)
        reply = f"Выберите предмет ({course_year.value}-й курс):\n"

        buttons = [
            InlineKeyboardButton(text=subject.name, callback_data=f"{data_parts[0]}/subject/{subject.id}")
            for subject in subjects
        ]
        await query.message.reply_text(reply if buttons else "Предметы по этому курсу ещё не добавили :(", reply_markup=InlineKeyboardMarkup([buttons]))
        return States.NOTE_SELECTION

    async def list_notes_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data_parts = query.data.split("/")
        if len(data_parts) != 3 or data_parts[0] != "buy" or data_parts[1] != "subject":
            return

        subject_id = data_parts[2]
        notes = self._purchase_service.get_notes(subject_id)
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
        buyer = Buyer(external_id=user.id, name=user.full_name)
        receipt = self._purchase_service.generate_purchase_receipt(note_id=note_id, buyer=buyer)
        print("Notify admin (stub):", receipt)
        await query.message.reply_text(f"Реквизиты для оплаты конспекта: {receipt.payment_details}")