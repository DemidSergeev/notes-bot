import logging
from ..ports.inbound import DataServicePort
from ..ports.outbound.persistence import CourseRepositoryPort, SubjectRepositoryPort, NoteRepositoryPort
from ..ports.outbound.storage import NoteStoragePort


logger = logging.getLogger(__name__)

class DataService(DataServicePort):
    def __init__(
        self,
        course_repo: CourseRepositoryPort,
        subject_repo: SubjectRepositoryPort,
        note_repo: NoteRepositoryPort,
        note_storage: NoteStoragePort
    ):
        self._course_repo = course_repo
        self._subject_repo = subject_repo
        self._note_repo = note_repo
        self._note_storage = note_storage

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

    def get_note_file(self, note_id):
        note = self._note_repo.get_by_id(note_id)
        
        if not note:
            raise ValueError(f"Note with id {note_id} does not exist.")

        note_file = self._note_storage.get_by_id(note.id)

        if not note_file:
            raise ValueError(f"Note file with id {note.id} does not exist in storage.")

        logger.debug("Retrieved note %s (UUID %s) from storage", note.title, note.id)

        return note_file 