from src.core.application.ports.inbound.commands import CourseCommandsPort
from src.core.application.ports.inbound import PurchaseServicePort
from src.core.domain.models import Note, Buyer


class CliCourseCommands(CourseCommandsPort):
    def __init__(self, purchase_service: PurchaseServicePort):
        self._purchase_service = purchase_service

    def list_courses(self):
        courses = self._purchase_service.get_courses()
        for course in courses:
            print(f"Course: {course.year.value}, ID: {course.id}")
            for subject in course.subjects:
                print(f"  Subject: {subject.name}, ID: {subject.id}")
        return courses

    def submit_purchase_request(self, note: Note, buyer: Buyer):
        receipt = self._purchase_service.generate_purchase_receipt(note, buyer)
        print(f"Receipt created: {receipt.id}")
        return receipt