import os
import logging
import json
import time
import uuid
import shutil
import shlex
from pathlib import Path

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler
)

from db import SessionLocal
from models import CourseA, CourseB, CourseC, CourseD, Coursework, Base
from sqlalchemy.exc import NoResultFound

# Логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# константы состояний ConversationHandler
CHOOSING_ACTION, CHOOSING_TYPE, CHOOSING_COURSE, CHOOSING_SUBJECT, SELL_UPLOAD, SELL_PAYDETAILS = range(6)

# директории
CHECK_DIR = Path("/app/check")
DATA_DIR = Path("/app/data/notes")
CHECK_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# окружение
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PAYMENT_DETAILS = os.getenv("PAYMENT_DETAILS", "Реквизиты для оплаты: ...")
WELCOME_FILE = Path("welcome.txt")
if not WELCOME_FILE.exists():
    WELCOME_FILE.write_text("Здравствуйте! Выберите действие:")

# в памяти - простые pending структуры (для примера)
pending_purchases = {}  # key: user_id -> dict with purchase info

# вспомогательные функции для выбора таблицы по курсу
COURSE_TABLES = {
    "Курс A": CourseA,
    "Курс B": CourseB,
    "Курс C": CourseC,
    "Курс D": CourseD,
}

def get_welcome_text():
    return WELCOME_FILE.read_text()

# ----- helper: safe answer for callback queries -----
async def safe_answer(callback_query, **kwargs):
    """
    Безопасно отвечает на CallbackQuery — игнорируем «Query is too old» и похожие BadRequest.
    """
    try:
        await callback_query.answer(**kwargs)
    except BadRequest as e:
        msg = str(e).lower()
        # игнорируем типичные benign ошибки
        if ("query is too old" in msg) or ("response timeout" in msg) or ("query id is invalid" in msg) or ("already answered" in msg) or ("button_data_invalid" in msg):
            logger.warning("Ignored BadRequest while answering callback: %s", e)
        else:
            logger.exception("BadRequest while answering callback: %s", e)

# ----- callback token helpers -----
def gen_token():
    return uuid.uuid4().hex[:8]

def store_callback(application, token, payload: dict):
    cb_map = application.bot_data.setdefault("cb_map", {})
    cb_map[token] = payload

def pop_callback(application, token):
    cb_map = application.bot_data.setdefault("cb_map", {})
    return cb_map.pop(token, None)

# ---------------- bot handlers ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Купить", callback_data="buy")],
        [InlineKeyboardButton("Продать", callback_data="sell")]
    ]
    await update.message.reply_text(get_welcome_text(), reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_ACTION

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    # отвечаем безопасно (не падаем, если callback устарел)
    await safe_answer(query)

    # ---- обработка кнопок "Назад" ----
    if data == "back_to_main":
        kb = [
            [InlineKeyboardButton("Купить", callback_data="buy")],
            [InlineKeyboardButton("Продать", callback_data="sell")]
        ]
        await query.edit_message_text(get_welcome_text(), reply_markup=InlineKeyboardMarkup(kb))
        return CHOOSING_ACTION

    if data == "back_to_buy_type":
        kb = [
            [InlineKeyboardButton("Конспект", callback_data="buy_notes")],
            [InlineKeyboardButton("Курсовая", callback_data="buy_coursework")]
        ]
        await query.edit_message_text("Выберите что хотите купить:", reply_markup=InlineKeyboardMarkup(kb))
        return CHOOSING_TYPE

    if data == "back_to_course_selection_buy":
        kb = [[InlineKeyboardButton(k, callback_data=f"buynotes_{k}")] for k in COURSE_TABLES.keys()]
        kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
        await query.edit_message_text("Выберите курс:", reply_markup=InlineKeyboardMarkup(kb))
        return CHOOSING_COURSE

    if data == "back_to_course_selection_sell":
        kb = [[InlineKeyboardButton(k, callback_data=f"sell_{k}")] for k in COURSE_TABLES.keys()]
        kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
        await query.edit_message_text("Выберите курс, по которому хотите продать конспект:", reply_markup=InlineKeyboardMarkup(kb))
        return CHOOSING_COURSE

    if data == "back_to_coursework_courses":
        s = SessionLocal()
        try:
            rows = s.query(Coursework.course).distinct().all()
            kb = [[InlineKeyboardButton(r[0], callback_data=f"buycw_{r[0]}")] for r in rows]
            kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_buy_type")])
            await query.edit_message_text("Выберите курс для курсовых:", reply_markup=InlineKeyboardMarkup(kb))
            return CHOOSING_COURSE
        finally:
            s.close()

    # основной роутинг
    if data == "buy":
        kb = [
            [InlineKeyboardButton("Конспект", callback_data="buy_notes")],
            [InlineKeyboardButton("Курсовая", callback_data="buy_coursework")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
        ]
        await query.edit_message_text(get_welcome_text(), reply_markup=InlineKeyboardMarkup(kb))
        return CHOOSING_ACTION

    if data == "sell":
        kb = [[InlineKeyboardButton(k, callback_data=f"sell_{k}")] for k in COURSE_TABLES.keys()]
        kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
        await query.edit_message_text("Выберите курс, по которому хотите продать конспект:", reply_markup=InlineKeyboardMarkup(kb))
        return CHOOSING_COURSE

    if data == "buy_notes":
        kb = [[InlineKeyboardButton(k, callback_data=f"buynotes_{k}")] for k in COURSE_TABLES.keys()]
        kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
        await query.edit_message_text("Выберите курс:", reply_markup=InlineKeyboardMarkup(kb))
        return CHOOSING_COURSE

    if data == "buy_coursework":
        s = SessionLocal()
        try:
            rows = s.query(Coursework.course).distinct().all()
            if not rows:
                await query.edit_message_text("Курсовые пока не добавлены.")
                return ConversationHandler.END
            kb = [[InlineKeyboardButton(r[0], callback_data=f"buycw_{r[0]}")] for r in rows]
            kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_buy_type")])
            await query.edit_message_text("Выберите курс для курсовых:", reply_markup=InlineKeyboardMarkup(kb))
            return CHOOSING_COURSE
        finally:
            s.close()

    # старые префиксы для выбора курса -> показываем предметы (перенаправляем к новым функциям)
    if data.startswith("buynotes_"):
        course = data.split("_", 1)[1]
        return await show_subjects_for_course(query, context, course, purpose="buy")

    if data.startswith("buycw_"):
        course = data.split("_", 1)[1]
        return await show_coursework_list(query, context, course)

    if data.startswith("sell_"):
        course = data.split("_", 1)[1]
        return await show_subjects_for_course(query, context, course, purpose="sell")

    # ---- новые токенизированные callback'ы: sd_ (subject), cw_ (coursework) ----
    if data.startswith("sd_") or data.startswith("cw_"):
        prefix, token = data.split("_", 1)
        payload = context.application.bot_data.get("cb_map", {}).get(token)
        if not payload:
            await query.edit_message_text("Кнопка устарела — пожалуйста, повторите действие.")
            return ConversationHandler.END

        ptype = payload.get("type")
        if ptype == "subject":
            course = payload["course"]
            subject = payload["subject"]
            purpose = payload.get("purpose", "buy")

            if purpose == "sell":
                # продавец: начинаем поток загрузки
                context.user_data["action"] = "sell"
                context.user_data["sell_course"] = course
                context.user_data["sell_subject"] = subject
                await query.edit_message_text(f"Отправьте PDF конспекта для {course} — {subject} (только .pdf). После файла отправьте свои реквизиты сообщением.")
                pop_callback(context.application, token)
                return SELL_UPLOAD
            else:
                # покупка: проверим таблицу
                s = SessionLocal()
                try:
                    table = COURSE_TABLES[course]
                    r = s.query(table).filter_by(subject=subject).one_or_none()
                    if r and r.has_note and r.pdf_filename:
                        pending_purchases[update.effective_user.id] = {
                            "course": course,
                            "subject": subject,
                            "file": r.pdf_filename
                        }

                        # --- Добавляем метаданные и уведомление админа ---
                        metadata = {
                            "buyer_id": update.effective_user.id,
                            "buyer_name": update.effective_user.full_name,
                            "course": course,
                            "subject": subject,
                            "file": r.pdf_filename,
                            "timestamp": int(time.time())
                        }
                        # сохраняем JSON на диск
                        json_path = DATA_DIR / f"purchase_{update.effective_user.id}_{int(time.time())}.json"
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)

                        # уведомляем админа
                        if ADMIN_ID:
                            await context.bot.send_message(
                                ADMIN_ID,
                                f"Новая покупка:\nФайл: {r.pdf_filename}\nМетаданные: {json.dumps(metadata, ensure_ascii=False)}"
                            )
                        # --- конец добавления ---

                        text = f"Для покупки конспекта по {subject}:\n{PAYMENT_DETAILS}\n\nПожалуйста, оплатите и дождитесь проверки (до 3 часов)."
                        await query.edit_message_text(text)
                        pop_callback(context.application, token)
                        return ConversationHandler.END
                    else:
                        await query.edit_message_text("По этому предмету конспекта пока нет.")
                        pop_callback(context.application, token)
                        return ConversationHandler.END
                finally:
                    s.close()

        if ptype == "coursework":
            course = payload["course"]
            cw_id = payload["cw_id"]
            s = SessionLocal()
            try:
                cw = s.query(Coursework).filter_by(id=cw_id).one_or_none()
                if not cw:
                    await query.edit_message_text("Курсовая не найдена.")
                    pop_callback(context.application, token)
                    return ConversationHandler.END
                if cw.pdf_filename:
                    await query.edit_message_text(f"Курсовая доступна. Реквизиты для оплаты:\n{PAYMENT_DETAILS}\nПроверка займет до 3 часов.")
                else:
                    await query.edit_message_text("По этой курсовой файла пока нет.")
                pop_callback(context.application, token)
                return ConversationHandler.END
            finally:
                s.close()

    # Fallback
    return ConversationHandler.END

async def show_subjects_for_course(query, context: ContextTypes.DEFAULT_TYPE, course=None, purpose="buy"):
    """
    Показываем список предметов для курса. Создаём короткие токены для кнопок и сохраняем payload в app.bot_data['cb_map'].
    """
    s = SessionLocal()
    try:
        table = COURSE_TABLES[course]
        rows = s.query(table).all()
        if not rows:
            await query.edit_message_text("Нет предметов в этом курсе.")
            return ConversationHandler.END
        kb = []
        for r in rows:
            mark = "✅" if r.has_note else "❌"
            token = gen_token()
            payload = {"type": "subject", "course": course, "subject": r.subject, "purpose": purpose}
            store_callback(context.application, token, payload)
            kb.append([InlineKeyboardButton(f"{mark} {r.subject}", callback_data=f"sd_{token}")])

        # добавляем кнопку назад в зависимости от purpose
        if purpose == "sell":
            kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_course_selection_sell")])
        else:
            kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_course_selection_buy")])

        await query.edit_message_text("Выберите предмет:\n(✅ — есть конспект, ❌ — нет)", reply_markup=InlineKeyboardMarkup(kb))
        return CHOOSING_SUBJECT
    finally:
        s.close()

async def show_coursework_list(query, context: ContextTypes.DEFAULT_TYPE, course=None):
    s = SessionLocal()
    try:
        rows = s.query(Coursework).filter_by(course=course).all()
        if not rows:
            await query.edit_message_text("Курсовые для этого курса не найдены.")
            return ConversationHandler.END
        kb = []
        for r in rows:
            token = gen_token()
            payload = {"type": "coursework", "course": course, "cw_id": r.id}
            store_callback(context.application, token, payload)
            kb.append([InlineKeyboardButton(r.title + (" ✅" if r.pdf_filename else " ❌"), callback_data=f"cw_{token}")])

        # кнопка назад — возвращаем к списку курсов для курсовых
        kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_coursework_courses")])

        await query.edit_message_text("Выберите курсовую:", reply_markup=InlineKeyboardMarkup(kb))
        return CHOOSING_SUBJECT
    finally:
        s.close()

# обработчик документов для продавца
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # только если в процессе продажи (SELL_UPLOAD)
    user_id = update.effective_user.id
    if context.user_data.get("sell_subject") is None:
        await update.message.reply_text("Я не ожидал файл. Начните /start и выберите 'Продать'.")
        return ConversationHandler.END

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Пожалуйста, отправьте файл в формате PDF.")
        return

    course = context.user_data["sell_course"]
    subject = context.user_data["sell_subject"]

    # сохранение файла в /app/check с понятным именем
    ts = int(time.time())
    filename = f"{course}__{subject}__user{user_id}__{ts}.pdf".replace(" ", "_")
    filepath = CHECK_DIR / filename
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(str(filepath))

    # ожидаем, чтобы пользователь прислал реквизиты как текст — сохраняем их вместе
    context.user_data["last_uploaded_file"] = filename
    await update.message.reply_text("Файл сохранён в очередь на проверку. Теперь, пожалуйста, отправьте сообщение с вашими реквизитами для оплаты (текст).")
    return SELL_PAYDETAILS

async def handle_sell_paydetails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    filename = context.user_data.get("last_uploaded_file")
    if not filename:
        await update.message.reply_text("Не нашёл загруженный файл. Пожалуйста, начните заново.")
        return ConversationHandler.END

    # сохраним метаданные рядом с файлом
    meta = {
        "uploader_id": update.effective_user.id,
        "uploader_name": update.effective_user.full_name,
        "course": context.user_data.get("sell_course"),
        "subject": context.user_data.get("sell_subject"),
        "payment_details": text,
        "timestamp": int(time.time())
    }
    meta_path = CHECK_DIR / (filename + ".json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    await update.message.reply_text("Спасибо — ваш файл ожидает ручной проверки. Администратор получит уведомление.")
    # оповестим администратора (если задан)
    if ADMIN_ID:
        try:
            await context.bot.send_message(ADMIN_ID, f"Новый файл на проверку: {filename}\nМетаданные: {json.dumps(meta, ensure_ascii=False)}")
        except Exception as e:
            logger.warning("Не удалось отправить сообщение администратору: %s", e)
    # очистим user_data продажи
    context.user_data.pop("sell_course", None)
    context.user_data.pop("sell_subject", None)
    context.user_data.pop("last_uploaded_file", None)
    return ConversationHandler.END

# --- Админ команды ----------------------------------------------------------------

async def admin_list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Только администратор.")
        return
    files = list(CHECK_DIR.glob("*.pdf"))
    if not files:
        await update.message.reply_text("Очередь пустая.")
        return
    msg = "Пайдинг файлы:\n" + "\n".join([f.name for f in files])
    await update.message.reply_text(msg)

async def admin_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ожидаем: /confirm <filename> <course> <subject>
    """
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Только администратор.")
        return

    # --- заменяем context.args на shlex.split ---
    try:
        # убираем сам '/confirm' и корректно разбиваем аргументы с кавычками
        args = shlex.split(update.message.text)[1:]
    except ValueError as e:
        await update.message.reply_text(f"Ошибка парсинга команды: {e}")
        return

    if len(args) < 3:
        await update.message.reply_text("Использование: /confirm <filename> <Курс A|Курс B|Курс C|Курс D> <subject>")
        return

    filename = args[0]
    course = args[1]
    subject = " ".join(args[2:])

    # дальше оставляем существующий код
    src = CHECK_DIR / filename
    logger.info("Ищу файл: %s", src)
    if not src.exists():
        await update.message.reply_text("Файл не найден в /check.")
        return

    dest = DATA_DIR / filename
    logger.info("Проверяю курс: %r", course)
    logger.info("Доступные курсы: %r", list(COURSE_TABLES.keys()))

    if course not in COURSE_TABLES:
        await update.message.reply_text("Неправильный курс.")
        return
    
    try:
        shutil.move(str(src), str(dest)) # перемещение
    except Exception as e:
        logger.error("Ошибка при перемещении файла: %s", e)
        await update.message.reply_text("Не удалось переместить файл. Проверьте права и доступность директорий.")
        return

    s = SessionLocal()
    try:
        table = COURSE_TABLES[course]
        obj = s.query(table).filter_by(subject=subject).one_or_none()
        if not obj:
            # создадим запись если не существует
            obj = table(subject=subject, has_note=True, pdf_filename=str(dest.name))
            s.add(obj)
        else:
            obj.has_note = True
            obj.pdf_filename = dest.name
        s.commit()
        await update.message.reply_text(f"Файл {filename} подтверждён и перемещён. Запись в БД обновлена.")
    finally:
        s.close()

async def admin_release(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /release <user_id> <course> <subject>
    Отправляет файл пользователю (если доступен).
    Поддерживает пробелы и кавычки в названии курса и предмета.
    """
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Только администратор.")
        return

    # Получаем текст команды без "/release "
    args_text = update.message.text[len("/release "):].strip()
    try:
        args = shlex.split(args_text)  # корректно разбивает с кавычками
    except ValueError as e:
        await update.message.reply_text(f"Ошибка разбора аргументов: {e}")
        return

    if len(args) < 3:
        await update.message.reply_text(
            "Использование: /release <user_id> <Курс A|Курс B|Курс C|Курс D> <subject>"
        )
        return

    # Разбираем аргументы
    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Неправильный user_id.")
        return

    course = args[1]
    subject = " ".join(args[2:])

    if course not in COURSE_TABLES:
        await update.message.reply_text("Неправильный курс.")
        return

    s = SessionLocal()
    try:
        table = COURSE_TABLES[course]
        obj = s.query(table).filter_by(subject=subject).one_or_none()
        if not obj or not obj.has_note or not obj.pdf_filename:
            await update.message.reply_text("Конспект не найден в БД.")
            return

        file_path = DATA_DIR / obj.pdf_filename
        if not file_path.exists():
            await update.message.reply_text("Файл отсутствует в хранилище.")
            return

        # Отправляем файл пользователю с правильным именем
        with open(file_path, "rb") as f:
            input_file = InputFile(f, filename=obj.pdf_filename)
            await context.bot.send_document(chat_id=user_id, document=input_file)

        await update.message.reply_text("Файл отправлен пользователю.")
    finally:
        s.close()

async def admin_set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Только администратор.")
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Использование: /set_welcome <текст>")
        return
    WELCOME_FILE.write_text(text)
    await update.message.reply_text("Приветственное сообщение обновлено.")

# cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    context.user_data.clear()
    return ConversationHandler.END

def build_app():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN не задан")
    app = ApplicationBuilder().token(token).build()

    # гарантируем, что карта callback'ов существует
    app.bot_data.setdefault("cb_map", {})

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_ACTION: [CallbackQueryHandler(callback_router)],
            CHOOSING_TYPE: [CallbackQueryHandler(callback_router)],
            CHOOSING_COURSE: [CallbackQueryHandler(callback_router)],
            CHOOSING_SUBJECT: [CallbackQueryHandler(callback_router)],
            SELL_UPLOAD: [MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_document)],
            SELL_PAYDETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sell_paydetails)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True,
        per_chat=False,
    )

    app.add_handler(conv)
    # админ команды
    app.add_handler(CommandHandler("list_pending", admin_list_pending))
    app.add_handler(CommandHandler("confirm", admin_confirm))
    app.add_handler(CommandHandler("release", admin_release))
    app.add_handler(CommandHandler("set_welcome", admin_set_welcome))
    return app

if __name__ == "__main__":
    # создадим таблицы, если нужно
    Base.metadata.create_all(bind=__import__("db").engine)
    app = build_app()
    logger.info("Bot started")
    app.run_polling()
