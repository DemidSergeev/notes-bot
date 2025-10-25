from ..ports.inbound import DataServicePort
from ..ports.outbound.persistence import CourseRepositoryPort, SubjectRepositoryPort, NoteRepositoryPort

class DataService(DataServicePort):
    def __init__(
        self,
        course_repo: CourseRepositoryPort,
        subject_repo: SubjectRepositoryPort,
        note_repo: NoteRepositoryPort,
    ):
        self._course_repo = course_repo
        self._subject_repo = subject_repo
        self._note_repo = note_repo

    def get_courses(self):
        return self._course_repo.get_all()

    def get_subjects(self, course_year):
        course = self._course_repo.get_by_year(course_year)

        if not course:
            raise ValueError(f"Course for year {course_year} does not exist.")

        return course.subjects

    def get_notes(self, subject_id):
        subject = self._subject_repo.get_by_id(subject_id)

        if not subject:
            raise ValueError(f"Subject with id {subject_id} does not exist.")

        return subject.notes