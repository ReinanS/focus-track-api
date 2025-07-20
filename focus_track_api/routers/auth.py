from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.database import get_session
from focus_track_api.models import User
from focus_track_api.schemas.token import Token
from focus_track_api.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)

router = APIRouter(prefix='/auth', tags=['auth'])

OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]
Session = Annotated[AsyncSession, Depends(get_session)]
UserId = Annotated[str, Depends(decode_refresh_token)]

@router.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2Form, session: Session):
    user = await session.scalar(
        select(User).where(User.email == form_data.username)
    )

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect email or password',
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect email or password',
        )

    access_token = create_access_token(data={'sub': str(user.id)})
    refresh_token = create_refresh_token(data={'sub': str(user.id)})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type='bearer'
    )


@router.post('/refresh', response_model=Token)
async def refresh_access_token(user_id: UserId):
    new_access_token = create_access_token(data={'sub': str(user_id)})
    refresh_token = create_refresh_token(data={'sub': str(user_id)})

    return Token(
        access_token=new_access_token,
        refresh_token=refresh_token,
        token_type='bearer'
    )
