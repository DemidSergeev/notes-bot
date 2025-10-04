import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://pguser:pgpass@db:5432/notesdb")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
