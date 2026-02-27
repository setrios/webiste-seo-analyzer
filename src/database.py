from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import create_engine, func
from datetime import datetime
from enum import Enum

DATABASE_URL = 'sqlite:///./my.db'

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


class JobStatus(str, Enum):
    CREATED = 'CREATED'
    QUEUED = 'QUEUED'
    PROCESSING = 'PROCESSING'
    DONE = 'DONE'
    ERROR = 'ERROR'


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = 'jobs'

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]
    status: Mapped[str] = mapped_column(default=JobStatus.CREATED.value)
    result: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())


