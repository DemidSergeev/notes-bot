from src.core.application.services import PurchaseService
from src.infrastructure.adapters.outbound.persistence import SqlModelCourseRepository, SqlModelSubjectRepository, SqlModelNoteRepository, SqlModelPurchaseReceiptRepository
from src.infrastructure.adapters.outbound.payment_details_provider import ConfigPaymentDetailsProvider
from src.infrastructure.adapters.inbound.telegram import TelegramHandlers
from src.infrastructure.adapters.inbound.telegram import Application
from src.infrastructure.config.database import get_session
from src.infrastructure.config import settings


note_repo = SqlModelNoteRepository(session_factory=get_session)
subject_repo = SqlModelSubjectRepository(session_factory=get_session, note_repository=note_repo)
course_repo = SqlModelCourseRepository(session_factory=get_session, subject_repository=subject_repo)
purchase_receipt_repo = SqlModelPurchaseReceiptRepository(session_factory=get_session)

purchase_service = PurchaseService(
    course_repo=course_repo,
    subject_repo=subject_repo,
    note_repo=note_repo,
    purchase_receipt_repo=purchase_receipt_repo,
    payment_details_provider=ConfigPaymentDetailsProvider(),
)

telegram_handlers = TelegramHandlers(
    purchase_service=purchase_service,
    welcome_message="Добро пожаловать в бот по покупке конспектов!"
)

application = Application(
    telegram_handlers=telegram_handlers,
    telegram_token=settings.TELEGRAM_BOT_TOKEN
)