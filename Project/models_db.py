from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Boolean, Date, DateTime, ForeignKey, JSON
from datetime import date, datetime


class Base(DeclarativeBase):
    pass


class DeveloperDB(Base):
    __tablename__ = "developers"

    id: Mapped[int] = mapped_column(primary_key=True)
    inn: Mapped[str] = mapped_column(String(12), unique=True)
    name: Mapped[str]
    registration_date: Mapped[date]


class RatingDB(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    developer_id: Mapped[int] = mapped_column(ForeignKey("developers.id"))
    score: Mapped[float]
    status: Mapped[str]
    rating_date: Mapped[date]


class DeveloperDossierDB(Base):
    __tablename__ = "developer_dossiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    developer_id: Mapped[int] = mapped_column(ForeignKey("developers.id"), unique=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str]
    details: Mapped[dict] = mapped_column(JSON)
    factors: Mapped[dict] = mapped_column(JSON)
    projects: Mapped[list] = mapped_column(JSON)
    legal_events: Mapped[list] = mapped_column(JSON)
    news: Mapped[list] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NewsSourceDB(Base):
    __tablename__ = "news_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    source_type: Mapped[str] = mapped_column(String(20), default="rss")
    url_template: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_query: Mapped[bool] = mapped_column(Boolean, default=False)
