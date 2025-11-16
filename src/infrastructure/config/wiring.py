import logging

from src.core.application.services import PurchaseService, DataService, SellService
from src.infrastructure.adapters.outbound.persistence import SqlModelCourseRepository, SqlModelSubjectRepository, SqlModelNoteRepository, SqlModelPurchaseReceiptRepository
from src.infrastructure.adapters.outbound.storage import MinioNoteStorage
from src.infrastructure.adapters.outbound.payment_details_provider import ConfigPaymentDetailsProvider
from src.infrastructure.adapters.inbound.telegram import TelegramHandlers
from src.infrastructure.adapters.inbound.telegram import Application
from src.infrastructure.config.database import get_session
from src.infrastructure.config.storage import get_client
from src.infrastructure.config import settings


logger = logging.getLogger(__name__)

note_repo = SqlModelNoteRepository(session_factory=get_session)
subject_repo = SqlModelSubjectRepository(session_factory=get_session, note_repository=note_repo)
course_repo = SqlModelCourseRepository(session_factory=get_session, subject_repository=subject_repo)
purchase_receipt_repo = SqlModelPurchaseReceiptRepository(session_factory=get_session)

note_storage = MinioNoteStorage(client=get_client(), bucket=settings.MINIO_BUCKET)

logger.debug("Repositories and storage wiring complete")

data_service = DataService(
    course_repo=course_repo,
    subject_repo=subject_repo,
    note_repo=note_repo,
    note_storage=note_storage
)

purchase_service = PurchaseService(
    note_repo=note_repo,
    purchase_receipt_repo=purchase_receipt_repo,
    payment_details_provider=ConfigPaymentDetailsProvider(),
)

sell_service = SellService(
    note_repo=note_repo,
    note_storage=note_storage
)

logger.debug("Services wiring complete")

telegram_handlers = TelegramHandlers(
    purchase_service=purchase_service,
    data_service=data_service,
    sell_service=sell_service,
    welcome_message="Добро пожаловать в бот по покупке конспектов!"
)

logger.debug("Telegram handlers wiring complete")

application = Application(
    telegram_handlers=telegram_handlers,
    telegram_token=settings.TELEGRAM_BOT_TOKEN
)

logger.debug("Application wiring complete")