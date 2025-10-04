import uuid
from sqlmodel import Session, select
from src.core.application.ports.outbound.database import CourseRepository, SubjectRepository
from src.core.domain.models import Course
from src.core.domain.common.enums import CourseYear
from .models import Course as DBCourse


class SqlModelCourseRepository(CourseRepository):
    def __init__(self, session: Session, subject_repository: SubjectRepository):
        self.session = session
        self.subject_repository = subject_repository

    async def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        db_course = await self.session.get(DBCourse, course_id)
        if not db_course:
            return None
        subjects = [
            await self.subject_repository.get_by_id(subject.id)
            for subject in db_course.subjects
        ]
        return Course(id=db_course.id, year=CourseYear(db_course.year), subjects=subjects)

    async def get_by_year(self, year: CourseYear) -> Course | None:
        statement = select(DBCourse).where(DBCourse.year == year.value)
        db_course = await self.session.exec(statement).first()
        if not db_course:
            return None
        subjects = [
            await self.subject_repository.get_by_id(subject.id)
            for subject in db_course.subjects
        ]
        return Course(id=db_course.id, year=year, subjects=subjects)

    async def save(self, course: Course) -> None:
        db_course = DBCourse(id=course.id, year=course.year.value)
        self.session.add(db_course)
        await self.session.commit()
        for subject in course.subjects:
            await self.subject_repository.save(subject)

    async def delete(self, course_id: uuid.UUID) -> None:
        db_course = await self.session.get(DBCourse, course_id)
        if db_course:
            self.session.delete(db_course)
            await self.session.commit()