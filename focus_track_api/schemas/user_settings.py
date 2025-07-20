from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserSettingsBase(BaseModel):

    fatigue_threshold: int
    distraction_threshold: int


class UserSettingsCreate(UserSettingsBase):
    user_id: UUID


class UserSettingsUpdate(UserSettingsBase):
    pass


class UserSettingsSchema(UserSettingsBase):
    id: UUID
    user_id: UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
