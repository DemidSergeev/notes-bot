from src.infrastructure.adapters.inbound.commands import CliCourseCommands
from src.core.application.services import PurchaseService
from src.core.application.ports.outbound.persistence import CourseRepositoryPort
from src.core.domain.models import Subject, Course
from src.core.domain.common.enums import CourseYear


class MockCourseRepository(CourseRepositoryPort):
    def get_all(self):
        return [
            Course(
                year=CourseYear.ONE,
                subjects=[
                    Subject(
                        name="Mock subject 1",
                        notes=[]
                    ),
                    Subject(
                        name="Mock subject 2",
                        notes=[]
                    )
                ]
            ),
            Course(
                year=CourseYear.TWO,
                subjects=[
                    Subject(
                        name="Mock subject 3",
                        notes=[]
                    ),
                    Subject(
                        name="Mock subject 4",
                        notes=[]
                    )
                ]
            )
        ]

course_repo = MockCourseRepository()

purchase_service = PurchaseService(
    course_repo=course_repo,
    note_repo=...,
    purchase_receipt_repo=...,
    payment_details_provider=...,
)

course_commands = CliCourseCommands(purchase_service)