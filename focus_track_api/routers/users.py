import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.database import get_session
from focus_track_api.models import User
from focus_track_api.schemas.shared import FilterPage, Message
from focus_track_api.schemas.users import (
    UserList,
    UserPublic,
    UserSchema,
)
from focus_track_api.security import (
    get_current_user,
    get_password_hash,
)
from focus_track_api.services.users import (
    create_user,
    delete_user_data,
    get_users_paginated,
    update_user_data,
)

router = APIRouter(prefix='/users', tags=['users'])
Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    '', status_code=status.HTTP_201_CREATED, response_model=UserPublic
)
async def create(
    user: UserSchema,
    session: Session,
):
    # Verifica se o username ou email já existem
    existing_user = await session.scalar(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )

    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Username already exists',
            )
        elif existing_user.email == user.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Email already exists',
            )

    hashed_user_data = user.model_copy()
    hashed_user_data.password = get_password_hash(user.password)

    created_user = await create_user(
        session=session, user_data=hashed_user_data
    )
    return created_user


@router.get('', response_model=UserList)
async def read_users(
    session: Session, filter_users: Annotated[FilterPage, Query()]
):
    users = await get_users_paginated(
        session=session, offset=filter_users.offset, limit=filter_users.limit
    )
    return {'users': users}


@router.put('/{user_id}', response_model=UserPublic)
async def update_user(
    user_id: uuid.UUID,
    user: UserSchema,
    session: Session,
    current_user: CurrentUser,
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not enough permissions',
        )

    return await update_user_data(session, user_id, user)


@router.delete('/{user_id}', response_model=Message)
async def delete_user(
    user_id: uuid.UUID,
    session: Session,
    current_user: CurrentUser,
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not enough permissions',
        )

    return await delete_user_data(session, current_user)
