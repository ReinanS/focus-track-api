from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserSchema(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    users: list[UserPublic]


class UserSettingsPublic(BaseModel):
    id: UUID
    user_id: UUID
    notifications_enabled: bool
    sounds_enabled: bool
    fatigue_threshold: int
    distraction_threshold: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
