"""FastAPI dependency injection for DB session."""

from sqlalchemy.orm import Session
from memory.models import get_engine, get_session_factory, init_db
import os

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./gyrofinance.db")

engine = init_db(DB_URL)
SessionLocal = get_session_factory(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
