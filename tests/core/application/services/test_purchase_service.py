import uuid
from pytest import fixture

from src.core.application.services import PurchaseService


@fixture(scope="module")
def purchase_service(mock_course_repo, mock_note_repo, mock_purchase_receipt_repo, payment_details_provider) -> PurchaseService:
    return PurchaseService(
        mock_course_repo,
        mock_note_repo,
        mock_purchase_receipt_repo,
        payment_details_provider
    )

class TestPurchaseService:
    def test_get_courses(self, purchase_service: PurchaseService) -> None:
        courses = purchase_service.get_courses()
        assert(len(courses) == 2)
        for c in courses:
            assert isinstance(c.id, uuid.UUID)
            assert(len(c.subjects) == 3)
            for s in c.subjects:
                assert isinstance(s.id, uuid.UUID)
                assert(len(s.notes) == 3)
                for n in s.notes:
                    assert isinstance(n.id, uuid.UUID)
                    assert(n.title in [f"Note{i+1}" for i in range(3)])
                    assert(1 <= n.price_rub <= 10)

    def test_generate_purchase_receipt(self, purchase_service: PurchaseService, notes, buyer):
        purchase_receipt = purchase_service.generate_purchase_receipt(notes[0], buyer)
        purchase_service._purchase_receipt_repo.save.assert_called_with(purchase_receipt)