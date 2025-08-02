from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserSettingsBase(BaseModel):
    fatigue_threshold: int = Field(gt=0, le=100)
    distraction_threshold: int = Field(gt=0, le=100)


class UserSettingsCreate(UserSettingsBase):
    user_id: UUID


class UserSettingsUpdate(BaseModel):
    fatigue_threshold: Optional[int] = Field(None, gt=0, le=100)
    distraction_threshold: Optional[int] = Field(None, gt=0, le=100)


class UserSettingsSchema(UserSettingsBase):
    id: UUID
    user_id: UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
