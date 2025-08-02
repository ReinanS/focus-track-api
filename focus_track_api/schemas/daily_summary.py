from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from focus_track_api.schemas.study_session import StudySessionSchema


class DailySummaryPublic(BaseModel):
    id: UUID
    user_id: UUID
    avg_fatigue: float
    avg_distraction: float
    focused_time: int  # Tempo focado em milissegundos
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DailySummaryCreate(BaseModel):
    user_id: UUID
    avg_fatigue: float = 0.0
    avg_distraction: float = 0.0
    focused_time: int = 0  # Tempo focado em milissegundos
    created_at: datetime


class DailySummarySchema(BaseModel):
    id: UUID
    user_id: UUID
    avg_fatigue: float
    avg_distraction: float
    focused_time: int  # Tempo focado em milissegundos
    updated_at: datetime
    breaks: Optional[int] = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DailyAndSessionResponse(BaseModel):
    daily_data: list[DailySummarySchema]
    session_data: list[StudySessionSchema]
