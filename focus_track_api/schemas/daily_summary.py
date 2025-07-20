from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from focus_track_api.schemas.study_session import StudySessionSchema


class DailySummaryPublic(BaseModel):
    id: UUID
    user_id: UUID
    date: date
    avg_fatigue: float
    avg_distraction: float
    focused_time_minutes: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DailySummaryCreate(BaseModel):
    user_id: UUID
    date: date
    avg_fatigue: float = 0.0
    avg_distraction: float = 0.0
    focused_time_minutes: int = 0


class DailySummarySchema(BaseModel):
    id: UUID
    user_id: UUID
    date: date
    avg_fatigue: float
    avg_distraction: float
    focused_time_minutes: int
    updated_at: datetime
    breaks: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)


class DailyAndSessionResponse(BaseModel):
    daily_data: list[DailySummarySchema]
    session_data: list[StudySessionSchema]
