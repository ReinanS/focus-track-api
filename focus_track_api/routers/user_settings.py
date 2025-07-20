from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.database import get_session
from focus_track_api.models import User
from focus_track_api.schemas.user_settings import (
    UserSettingsCreate,
    UserSettingsSchema,
    UserSettingsUpdate,
)
from focus_track_api.security import get_current_user
from focus_track_api.services.user_settings import (
    create_user_settings,
    get_user_settings,
    update_user_settings,
)

router = APIRouter(prefix="/settings", tags=["user_settings"])
Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Depends(get_current_user)

@router.post("", response_model=UserSettingsSchema, status_code=HTTPStatus.CREATED)
async def create_settings(
    session: Session,
    current_user: User = CurrentUser,
    ):
    return await create_user_settings(current_user.id, session)


@router.get("", response_model=UserSettingsSchema)
async def read_settings(
    session: Session,
    current_user: User = CurrentUser,
    ):
    return await get_user_settings(current_user.id, session)


@router.put("", response_model=UserSettingsSchema)
async def update_settings(
    data: UserSettingsUpdate, 
    session: Session, 
    current_user: User = CurrentUser, 
    ):
    return await update_user_settings(current_user.id, data, session)
