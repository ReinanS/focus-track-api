import uuid
from datetime import date as dt
from datetime import datetime
from typing import List

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship

table_registry = registry()


@table_registry.mapped_as_dataclass
class User:
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), init=False, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())

    settings: Mapped["UserSettings"] = relationship(
        back_populates="user",
        init=False
    )
    summaries: Mapped[List["DailySummary"]] = relationship(
        back_populates="user",
        default_factory=list,
        init=False
    )
    sessions: Mapped[List["StudySession"]] = relationship(
        back_populates="user",
        default_factory=list,
        init=False
    )


@table_registry.mapped_as_dataclass
class UserSettings:
    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), init=False, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), init=False, unique=True)
    user: Mapped["User"] = relationship(back_populates="settings")
    fatigue_threshold: Mapped[int] = mapped_column(default=60)
    distraction_threshold: Mapped[int] = mapped_column(default=50)
    updated_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now(), onupdate=func.now())

@table_registry.mapped_as_dataclass
class DailySummary:
    __tablename__ = "daily_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), init=False, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="summaries", init=False)
    sessions: Mapped[list["StudySession"]] = relationship(back_populates="daily_summary", init=False)
    avg_fatigue: Mapped[float] = mapped_column(default=0.0)
    avg_distraction: Mapped[float] = mapped_column(default=0.0)
    focused_time_minutes: Mapped[int] = mapped_column(default=0)
    date: Mapped[dt] = mapped_column(default=dt.today)
    updated_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now(), onupdate=func.now())


@table_registry.mapped_as_dataclass
class StudySession:
    __tablename__ = "study_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), init=False, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    daily_summary_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("daily_summaries.id"))
    user: Mapped["User"] = relationship(back_populates="sessions", init=False)
    daily_summary: Mapped["DailySummary"] = relationship(back_populates="sessions", init=False)
    start_time: Mapped[datetime] = mapped_column(
        default=datetime.now(),
        server_default=func.now(),
        nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(
        init=False,
        onupdate=func.now(),
        nullable=True
    )
    duration_minutes: Mapped[int] = mapped_column(default=0)
    average_attention_score: Mapped[float] = mapped_column(default=0.0)
    average_fatigue: Mapped[float] = mapped_column(default=0.0)
    average_distraction: Mapped[float] = mapped_column(default=0.0)
    distraction_rate: Mapped[float] = mapped_column(default=0.0)
    max_fatigue: Mapped[float] = mapped_column(default=0.0)
    max_distraction: Mapped[float] = mapped_column(default=0.0)
    perclos: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())
