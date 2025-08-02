import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.models import User, UserSettings
from focus_track_api.schemas.users import UserSchema
from focus_track_api.security import get_password_hash


async def create_user(session: AsyncSession, user_data: UserSchema) -> User:
    new_user = User(**user_data.model_dump())
    session.add(new_user)
    await session.flush()

    settings = UserSettings(user=new_user)
    session.add(settings)

    await session.commit()
    await session.refresh(new_user)
    return new_user


async def get_users_paginated(
    session: AsyncSession,
    offset: int,
    limit: int,
) -> list[User]:
    result = await session.execute(select(User).offset(offset).limit(limit))
    return result.scalars().all()


async def update_user_data(
    session: AsyncSession,
    user_id: uuid.UUID,
    update_data: UserSchema,
) -> User:
    user = await session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found'
        )

    user.username = update_data.username
    user.email = update_data.email
    user.password = get_password_hash(update_data.password)

    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Username or Email already exists',
        )


async def delete_user_data(
    session: AsyncSession,
    user: User,
) -> dict:
    await session.delete(user)
    await session.commit()
    return {'message': 'User deleted'}
