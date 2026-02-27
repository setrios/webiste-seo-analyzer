from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime

DATABASE_URL = 'sqlite:///./my.db'

engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = 'jobs'

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]
    status: Mapped[str]
    result: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]


SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)