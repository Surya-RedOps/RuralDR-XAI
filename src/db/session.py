"""
RuralDR-XAI: Database Session & Engine Configuration (SIH26038)
Connects to primary MySQL 8.x instance with automatic SQLite fallback for isolated unit testing.
"""

import os
import logging
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

logger = logging.getLogger("ruraldr.db")

# Default fallback SQLite path in project data directory
DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_DB_DIR / 'ruraldr.db'}"

# Environment configuration
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    DATABASE_URL = DEFAULT_SQLITE_URL

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    engine_kwargs["pool_recycle"] = 3600
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        **engine_kwargs,
    )
    with engine.connect() as conn:
        pass
    logger.info(f"Connected to database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'local sqlite'}")
except Exception as e:
    logger.warning(f"Could not connect to primary DATABASE_URL ({e}). Falling back to local SQLite.")
    DATABASE_URL = DEFAULT_SQLITE_URL
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a thread-safe database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes all database tables and seeds foundational structural metadata."""
    from . import models  # Ensure all 18 models are registered with Base metadata
    Base.metadata.create_all(bind=engine)
    from .seed import seed_initial_data
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()
