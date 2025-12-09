import pytest
from unittest.mock import MagicMock
from sqlmodel import Session

from src.infrastructure.adapters.outbound.persistence import SqlModelCourseRepository
from src.core.domain.models import Course
from src.core.domain.common.enums import CourseYear
from src.infrastructure.adapters.outbound.persistence.models import Course as DbCourse


@pytest.fixture
def mock_subject_repo() -> MagicMock:
    """Create a mock SubjectRepository."""
    return MagicMock()


@pytest.fixture
def mock_session_factory():
    """Create a properly mocked session factory that handles context manager protocol."""
    mock_session = MagicMock(spec=Session)
    mock_factory = MagicMock()
    
    # Setup context manager behavior
    mock_factory.return_value.__enter__.return_value = mock_session
    mock_factory.return_value.__exit__.return_value = None
    
    # Attach the session for easy access in tests
    mock_factory._session = mock_session
    
    return mock_factory


@pytest.fixture
def course_repository(mock_session_factory, mock_subject_repo) -> SqlModelCourseRepository:
    """Create CourseRepository with mocked session factory and subject repo."""
    return SqlModelCourseRepository(
        session_factory=mock_session_factory,
        subject_repository=mock_subject_repo
    )


class TestSqlModelCourseRepositoryGetMethods:
    """Test get methods."""

    def test_get_by_id_success(self, course_repository, course_id, db_course, mock_session_factory):
        """Test retrieving a course by ID."""
        mock_session_factory._session.get.return_value = db_course
        
        result = course_repository.get_by_id(course_id)
        
        assert isinstance(result, Course)
        assert result.id == course_id
        assert result.year == CourseYear.TWO
        mock_session_factory._session.get.assert_called_once_with(DbCourse, course_id)

    def test_get_by_id_not_found(self, course_repository, course_id, mock_session_factory):
        """Test retrieving a non-existent course by ID."""
        mock_session_factory._session.get.return_value = None
        
        result = course_repository.get_by_id(course_id)
        
        assert result is None

    def test_get_by_year_success(self, course_repository, db_course, mock_session_factory):
        """Test retrieving a course by year."""
        mock_session_factory._session.exec.return_value.first.return_value = db_course
        
        result = course_repository.get_by_year(CourseYear.TWO)
        
        assert isinstance(result, Course)
        assert result.year == CourseYear.TWO

    def test_get_by_year_not_found(self, course_repository, mock_session_factory):
        """Test retrieving a course with year that doesn't exist."""
        mock_session_factory._session.exec.return_value.first.return_value = None
        
        result = course_repository.get_by_year(CourseYear.ONE)
        
        assert result is None

    def test_get_all_success(self, course_repository, db_courses, mock_session_factory):
        """Test retrieving all courses."""
        mock_session_factory._session.exec.return_value.all.return_value = db_courses
        
        result = course_repository.get_all()
        
        assert len(result) == 3
        assert all(isinstance(c, Course) for c in result)

    def test_get_all_empty(self, course_repository, mock_session_factory):
        """Test retrieving all courses when none exist."""
        mock_session_factory._session.exec.return_value.all.return_value = []
        
        result = course_repository.get_all()
        
        assert result == []


class TestSqlModelCourseRepositorySaveMethods:
    """Test save methods."""

    def test_save_new_course(self, course_repository, course, mock_session_factory):
        """Test saving a new course."""
        mock_session_factory._session.get.return_value = None  # Course doesn't exist
        
        course_repository.save(course)
        
        mock_session_factory._session.add.assert_called_once()
        mock_session_factory._session.commit.assert_called_once()

    def test_save_existing_course(self, course_repository, course, mock_session_factory):
        """Test updating an existing course."""
        db_course = MagicMock(spec=DbCourse)
        db_course.id = course.id
        db_course.year = course.year.value
        mock_session_factory._session.get.return_value = db_course  # Course exists
        
        course_repository.save(course)
        
        assert db_course.year == course.year.value
        mock_session_factory._session.add.assert_not_called()  # Should not add when updating
        mock_session_factory._session.commit.assert_called_once()

    def test_save_updates_subjects(self, course_repository, course, mock_session_factory, mock_subject_repo):
        """Test that save calls subject repository for each subject."""
        mock_session_factory._session.get.return_value = None
        
        course_repository.save(course)
        
        # Verify subject_repo.save was called for each subject
        assert mock_subject_repo.save.call_count == len(course.subjects)


class TestSqlModelCourseRepositoryDeleteMethods:
    """Test delete methods."""

    def test_delete_success(self, course_repository, course_id, mock_session_factory):
        """Test deleting an existing course."""
        db_course = MagicMock(spec=DbCourse)
        db_course.year = CourseYear.TWO.value
        mock_session_factory._session.get.return_value = db_course
        
        course_repository.delete(course_id)
        
        mock_session_factory._session.delete.assert_called_once_with(db_course)
        mock_session_factory._session.commit.assert_called_once()

    def test_delete_non_existent_course(self, course_repository, course_id, mock_session_factory):
        """Test deleting a non-existent course."""
        mock_session_factory._session.get.return_value = None
        
        course_repository.delete(course_id)
        
        # Should not call delete if course doesn't exist
        mock_session_factory._session.delete.assert_not_called()
        mock_session_factory._session.commit.assert_not_called()
