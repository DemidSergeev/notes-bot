import random
from pytest import fixture
from unittest.mock import MagicMock

from src.core.domain.models import Course, Subject, Note, User, PurchaseReceipt
from src.core.domain.common.enums import CourseYear
from src.core.application.ports.outbound.persistence import CourseRepositoryPort, SubjectRepositoryPort, NoteRepositoryPort, PurchaseReceiptRepositoryPort
from src.core.application.services.data import CourseService, SubjectService, NoteService, PurchaseReceiptService
from src.core.application.ports.outbound import PaymentDetailsProviderPort


@fixture(scope="module")
def notes() -> list[Note]:
    notes = []
    for i in range(3):
        notes.append(Note(f"Note{i+1}", random.randint(1, 10)))
    return notes

@fixture(scope="module")
def subjects(notes) -> list[Subject]:
    subjects = []
    for i in range(3):
        subjects.append(Subject(f"Subject{i+1}", notes))
    return subjects

@fixture(scope="module")
def course(subjects):
    return Course(CourseYear.TWO, subjects)

@fixture(scope="module")
def buyer():
    external_id = 1234567890
    name = "John Doe"
    return User(external_id, name)

@fixture(scope="module")
def payment_details_provider():
    provider = MagicMock(spec=PaymentDetailsProviderPort)
    provider.get.return_value = "6666 6666 6666 6666"
    return provider

@fixture(scope="module")
def purchase_receipt(buyer, payment_details_provider, notes):
    payment_details = payment_details_provider.get()
    return PurchaseReceipt(buyer, payment_details, notes[0])

@fixture(scope="module")
def mock_course_repo(course):
    repo = MagicMock(spec=CourseRepositoryPort)
    repo.get_by_id.return_value = course
    repo.get_by_year.return_value = course
    repo.get_all.return_value = [course, course]
    repo.save.return_value = None
    repo.delete.return_value = None
    return repo

@fixture(scope="module")
def mock_subject_repo(subjects):
    repo = MagicMock(spec=SubjectRepositoryPort)
    repo.get_by_id.return_value = subjects[0]
    repo.get_by_name.return_value = subjects[0]
    repo.save.return_value = None
    repo.delete.return_value = None
    return repo

@fixture(scope="module")
def mock_note_repo(notes):
    repo = MagicMock(spec=NoteRepositoryPort)
    repo.get_by_id.return_value = notes[0]
    repo.get_by_title.return_value = notes[0]
    repo.save.return_value = None
    repo.delete.return_value = None
    return repo

@fixture(scope="module")
def mock_purchase_receipt_repo(purchase_receipt):
    repo = MagicMock(spec=PurchaseReceiptRepositoryPort)
    repo.get_by_id.return_value = purchase_receipt
    repo.get_by_buyer_id.return_value = purchase_receipt
    repo.save.return_value = None
    repo.delete.return_value = None
    return repo