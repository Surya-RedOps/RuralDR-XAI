"""
RuralDR-XAI: Database Session & Engine Configuration
Supports MySQL with automatic SQLite fallback for testing and development.
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
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    # Test connection
    with engine.connect() as conn:
        pass
    logger.info(f"Database connected using: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'local sqlite'}")
except Exception as e:
    logger.warning(f"Failed to connect to primary DATABASE_URL ({e}). Falling back to local SQLite.")
    DATABASE_URL = DEFAULT_SQLITE_URL
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes all database tables and seeds demo records."""
    from . import models  # Ensure all models are registered
    Base.metadata.create_all(bind=engine)
    from .seed import seed_initial_data
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()
