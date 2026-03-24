"""Sync SQLAlchemy — Vercel serverless uyumlu."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator
from config.settings import settings

# aiosqlite → sync sqlite veya postgresql
_url = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite").replace("postgresql+asyncpg", "postgresql")

engine = create_engine(
    _url,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in _url else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
