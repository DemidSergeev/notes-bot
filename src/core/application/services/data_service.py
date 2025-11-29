import logging

from src.core.domain.models import Subject, Note
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


    # Get entities

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

    def get_approved_notes_by_subject_id(self, subject_id):
        notes = self._note_repo.get_approved_by_subject_id(subject_id)

        if not notes:
            logger.debug("No approved notes found")

        return notes

    def get_not_approved_notes(self):
        notes = self._note_repo.get_not_approved()

        if not notes:
            logger.debug("No not approved notes found")

        return notes

    def get_note_by_id(self, note_id):
        note = self._note_repo.get_by_id(note_id)

        if not note:
            raise ValueError(f"Note with id {note_id} does not exist.")
        
        return note

    def get_note_file(self, note_id):
        note = self._note_repo.get_by_id(note_id)
        
        if not note:
            raise ValueError(f"Note with id {note_id} does not exist.")

        note_file = self._note_storage.get_by_id(note.id)

        if not note_file:
            raise ValueError(f"Note file with id {note.id} does not exist in storage.")

        logger.debug("Retrieved note %s (UUID %s) from storage", note.title, note.id)

        return note_file 

    def get_note_url(self, note_id):
        note = self._note_repo.get_by_id(note_id)
        
        if not note:
            raise ValueError(f"Note with id {note_id} does not exist.")

        note_url = self._note_storage.get_url(note.id, note.title)

        if not note_url:
            raise ValueError(f"Note URL with id {note.id} does not exist in storage.")

        logger.debug("Retrieved note URL %s (title %s, UUID %s) from storage", note_url, note.title, note.id)

        return note_url


    # Create/update entities

    def add_subject(self, course_year, name):  
        course = self._course_repo.get_by_year(course_year)

        if not course:
            raise ValueError(f"Course for year {course_year} does not exist.")

        subject = Subject(
            name=name
        )

        self._subject_repo.save(subject, course.id)

        logger.debug("Added subject %s to course year %d", subject.name, course.year.value)

        return subject

    def upload_note(self, title, subject_id, file):
        note = Note(
            title=title,
        )
        file.seek(0)
        self._note_repo.save(note, subject_id)
        self._note_storage.save(note, file)
        logger.debug("Note %s (UUID %s) uploaded", title, note.id)


    # Delete entities

    def delete_subject(self, subject_id):
        subject = self._subject_repo.get_by_id(subject_id)

        if not subject:
            raise ValueError(f"Subject with id {subject_id} does not exist.")

        self._subject_repo.delete(subject_id)

        logger.debug("Deleted subject %s (UUID %s)", subject.name, subject.id)

    def delete_note(self, note_id):
        note = self._note_repo.get_by_id(note_id)

        if not note:
            raise ValueError(f"Note with id {note_id} does not exist.")

        self._note_repo.delete(note_id)

        logger.debug("Deleted note %s (UUID %s)", note.title, note.id)