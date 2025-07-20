from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StudySessionPublic(BaseModel):
    id: UUID
    user_id: UUID
    daily_summary_id: UUID
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    average_attention_score: float
    average_fatigue: float
    average_distraction: float
    distraction_rate: float
    max_fatigue: float
    max_distraction: float
    perclos: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudySessionCreate(BaseModel):
    user_id: UUID = None
    daily_summary_id: UUID = None
    duration_minutes: int = 0
    average_attention_score: float = 0.0
    average_fatigue: float = 0.0
    average_distraction: float = 0.0
    distraction_rate: float = 0.0
    max_fatigue: float = 0.0
    max_distraction: float = 0.0
    perclos: float = 0.0


class StudySessionSchema(BaseModel):
    id: UUID
    user_id: UUID
    daily_summary_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int
    average_attention_score: float
    average_fatigue: float
    average_distraction: float
    distraction_rate: float
    max_fatigue: float
    max_distraction: float
    perclos: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
