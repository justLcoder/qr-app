"""SQLAlchemy database setup and FastAPI request-scoped sessions.

The module creates the shared SQLAlchemy engine from configured settings and
defines ``Base``, the parent class used by ORM models. ``get_db`` is injected
into route handlers so each request receives a session that is closed after
the handler finishes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import get_settings

settings = get_settings()
# SQLite has a thread restriction that does not apply to PostgreSQL. This
# option supports the local SQLite fallback and is deliberately omitted for
# the normal PostgreSQL connection.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    # ``yield`` makes this a FastAPI dependency with teardown: FastAPI resumes
    # the generator after the route and always closes the connection session.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
