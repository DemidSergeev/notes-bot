"""Fixtures for integration tests using testcontainers."""

from time import sleep

import pytest
from sqlmodel import Session, SQLModel, create_engine
from minio import Minio
from testcontainers.postgres import PostgresContainer
from testcontainers.minio import MinioContainer

from src.infrastructure.adapters.outbound.persistence import (
    SqlModelCourseRepository,
    SqlModelSubjectRepository,
    SqlModelNoteRepository,
)
from src.infrastructure.adapters.outbound.storage import MinioNoteStorage


# ============================================================================
# CONTAINER FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def postgres_container():
    """Start a PostgreSQL container for the session."""
    container = PostgresContainer("postgres:15")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def minio_container():
    """Start a MinIO container for the session."""
    container = MinioContainer()
    container.start()
    yield container
    container.stop()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def postgres_engine(postgres_container):
    """Create a SQLAlchemy engine for the test database."""
    # Build the PostgreSQL connection string
    url = postgres_container.get_connection_url()
    # Replace psycopg2 with psycopg (v3) driver
    url = url.replace("psycopg2", "psycopg")
    
    engine = create_engine(url, echo=False)
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    engine.dispose()


@pytest.fixture
def session_factory(postgres_engine):
    """Create a session factory for repositories."""
    from contextlib import contextmanager
    
    @contextmanager
    def get_session():
        session = Session(postgres_engine)
        try:
            yield session
        finally:
            session.close()
    
    return get_session


@pytest.fixture
def db_session(postgres_engine):
    """Create a database session for tests."""
    session = Session(postgres_engine)
    yield session
    session.close()


@pytest.fixture(autouse=True)
def cleanup_database(postgres_engine):
    """Clean up database after each test for isolation."""
    yield
    # Clean up all tables after the test
    from src.infrastructure.adapters.outbound.persistence.models import (
        Course as DbCourse,
        Subject as DbSubject,
        Note as DbNote,
    )
    from sqlmodel import delete
    
    with Session(postgres_engine) as session:
        # Delete in reverse order of foreign key dependencies
        session.exec(delete(DbNote))
        session.exec(delete(DbSubject))
        session.exec(delete(DbCourse))
        session.commit()


# ============================================================================
# MINIO FIXTURES
# ============================================================================

@pytest.fixture
def minio_client(minio_container):
    """Create a MinIO client connected to the test container."""
    # MinIO container provides connection parameters via environment variables
    # The container exposes itself via localhost
    host = minio_container.get_container_host_ip()
    port = minio_container.get_exposed_port(9000)
    
    client = Minio(
        endpoint=f"{host}:{port}",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False,
    )
    
    yield client


@pytest.fixture
def minio_bucket_name():
    """Return the bucket name for tests."""
    return "test-notes"


@pytest.fixture
def minio_bucket(minio_client, minio_bucket_name):
    """Create a test bucket in MinIO."""
    # Wait a bit for MinIO to be ready
    sleep(1)
    
    found = minio_client.bucket_exists(minio_bucket_name)
    if not found:
        minio_client.make_bucket(minio_bucket_name)
    
    yield minio_bucket_name
    
    # Cleanup: remove all objects and the bucket
    try:
        objects = minio_client.list_objects(minio_bucket_name, recursive=True)
        for obj in objects:
            minio_client.remove_object(minio_bucket_name, obj.object_name)
        minio_client.remove_bucket(minio_bucket_name)
    except Exception:
        pass


# ============================================================================
# REPOSITORY FIXTURES
# ============================================================================

@pytest.fixture
def course_repo(session_factory):
    """Create a CourseRepository for testing."""
    subject_repo = SqlModelSubjectRepository(session_factory=session_factory, note_repository=None)
    return SqlModelCourseRepository(session_factory=session_factory, subject_repository=subject_repo)


@pytest.fixture
def subject_repo(session_factory):
    """Create a SubjectRepository for testing."""
    note_repo = SqlModelNoteRepository(session_factory=session_factory)
    return SqlModelSubjectRepository(session_factory=session_factory, note_repository=note_repo)


@pytest.fixture
def note_repo(session_factory):
    """Create a NoteRepository for testing."""
    return SqlModelNoteRepository(session_factory=session_factory)


@pytest.fixture
def note_storage(minio_client, minio_bucket):
    """Create a MinioNoteStorage for testing."""
    return MinioNoteStorage(
        client=minio_client,
        bucket=minio_bucket,
        url_signer_client=minio_client
    )


# ============================================================================
# DOMAIN MODEL FIXTURES - Inherited from parent conftest.py
# ============================================================================
# The following fixtures are already defined in tests/conftest.py and are
# automatically available here through pytest's fixture discovery:
# - note_id, subject_id, course_id
# - note, approved_note, notes
# - subject, subjects
# - course, courses
# - note_file (as pdf_file or text_file)
#
# We reuse these fixtures instead of redefining them to avoid duplication.
