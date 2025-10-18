from src.infrastructure.adapters.inbound.commands import CliCourseCommands
from src.core.application.services import PurchaseService
from src.core.application.services.data import CourseService, PurchaseReceiptService
from src.infrastructure.adapters.outbound.persistence import SqlModelCourseRepository, SqlModelSubjectRepository, SqlModelNoteRepository, SqlModelPurchaseReceiptRepository
from src.infrastructure.adapters.outbound.payment_details_provider import ConfigPaymentDetailsProvider
from src.infrastructure.config.database import get_session


note_repo = SqlModelNoteRepository(session_factory=get_session)
subject_repo = SqlModelSubjectRepository(session_factory=get_session, note_repository=note_repo)
course_repo = SqlModelCourseRepository(session_factory=get_session, subject_repository=subject_repo)
purchase_receipt_repo = SqlModelPurchaseReceiptRepository(session_factory=get_session)

course_service = CourseService(course_repo=course_repo, subject_repo=subject_repo)
purchase_receipt_service = PurchaseReceiptService(purchase_receipt_repo=purchase_receipt_repo)

purchase_service = PurchaseService(
    course_service=course_service,
    purchase_receipt_service=purchase_receipt_service,
    payment_details_provider=ConfigPaymentDetailsProvider(),
)

course_commands = CliCourseCommands(purchase_service)