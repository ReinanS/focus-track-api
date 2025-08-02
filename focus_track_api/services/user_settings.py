from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.models import UserSettings
from focus_track_api.schemas.user_settings import (
    UserSettingsCreate,
    UserSettingsUpdate,
)


async def create_user_settings(
    data: UserSettingsCreate, session: AsyncSession
) -> UserSettings:
    exists = await session.scalar(
        select(UserSettings).where(UserSettings.user_id == data.user_id)
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Settings already exist for this user',
        )

    settings = UserSettings(**data.model_dump())
    session.add(settings)
    await session.commit()
    await session.refresh(settings)
    return settings


async def get_user_settings(
    user_id: UUID, session: AsyncSession
) -> UserSettings:
    settings = await session.scalar(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User settings not found',
        )
    return settings


async def update_user_settings(
    user_id: UUID,
    data: UserSettingsUpdate,
    session: AsyncSession,
) -> UserSettings:
    settings = await session.scalar(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User settings not found',
        )

    for field, value in data.model_dump().items():
        if value is not None:
            setattr(settings, field, value)

    await session.commit()
    await session.refresh(settings)
    return settings
