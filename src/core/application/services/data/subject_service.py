import uuid
from src.core.domain.models import Subject, Note
from src.core.application.ports.outbound.persistence import SubjectRepositoryPort, CourseRepositoryPort, NoteRepositoryPort


class SubjectService:
    def __init__(self, subject_repo: SubjectRepositoryPort, course_repo: CourseRepositoryPort, note_repo: NoteRepositoryPort):
        self._subject_repo = subject_repo
        self._course_repo = course_repo
        self._note_repo = note_repo

    def create(self, name: str, course_id: uuid.UUID, notes: list[Note] = []) -> Subject:
        if not self._course_repo.get_by_id(course_id):
            raise ValueError(f"Course with id {course_id} does not exist.")
        

        subject = Subject(
            name=name,
            notes=notes
        )

        self._subject_repo.save(subject, course_id)
        for note in notes:
            self._note_repo.save(note, subject.id)

        return subject

    def get_by_id(self, subject_id: uuid.UUID) -> Subject | None:
        return self._subject_repo.get_by_id(subject_id)

    def get_by_name(self, name: str) -> Subject | None:
        return self._subject_repo.get_by_name(name)

    def delete(self, subject_id: uuid.UUID) -> None:
        self._subject_repo.delete(subject_id)