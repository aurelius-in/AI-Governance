from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import redis
from typing import Generator

from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.POSTGRES_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Create metadata
metadata = MetaData()

# Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis() -> redis.Redis:
    """Dependency to get Redis client"""
    return redis_client

# Database utilities
def init_db() -> None:
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def drop_db() -> None:
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)
