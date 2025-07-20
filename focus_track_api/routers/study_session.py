import time
from http import HTTPStatus
from typing import Annotated

from click import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.database import get_session
from focus_track_api.models import StudySession, User
from focus_track_api.schemas.session_metrics import SessionMetrics
from focus_track_api.schemas.study_session import (
    StudySessionCreate,
    StudySessionSchema,
)
from focus_track_api.security import get_current_user
from focus_track_api.services.attention import (
    finalize_session,
    start_study_session,
)
from focus_track_api.services.attention_scorer import AttentionScorer
from focus_track_api.services.study_session import (
    create_study_session,
    get_study_session,
)

router = APIRouter(prefix="/study-session", tags=["study-session"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=StudySessionSchema, status_code=HTTPStatus.CREATED)
async def create_study_session_endpoint(
    session_data: StudySessionCreate,
    session: Session,
    current_user: CurrentUser,
):
    return await create_study_session(
        session=session,
        session_data=session_data.model_copy(update={"user_id": current_user.id}),
    )


@router.get("", response_model=list[StudySessionSchema])
async def list_study_sessions(
    session: Session,
    current_user: CurrentUser,
):
    result = await session.execute(
        select(StudySession).where(StudySession.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{session_id}", response_model=StudySessionSchema)
async def get_study_session_endpoint(
    db: Session,
    current_user: CurrentUser,
    session_id: str,
):
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")

    study_session = await get_study_session(db, session_uuid)

    if not study_session or study_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Sessão de estudo não encontrada.")

    return study_session


@router.post("/start", response_model=StudySessionSchema, status_code=HTTPStatus.CREATED)
async def start_study_session_endpoint(
    db: Session,
    current_user: CurrentUser,
):
    session = await start_study_session(db, current_user)
    return session


@router.post("/finalize/{session_id}", status_code=HTTPStatus.OK)
async def finalize_study_session_endpoint(
    session_id: str,
    db: Session,
    current_user: CurrentUser,
):
    study_session = await get_study_session(db, UUID(session_id))

    if not study_session:
        raise HTTPException(status_code=404, detail="Sessão de estudo não encontrada.")

    scorer = AttentionScorer(t_now=time.perf_counter())
    await finalize_session(
        session=db,
        user=current_user,
        study_session=study_session,
        metrics=SessionMetrics(),
        scorer=scorer,
        start_time=study_session.start_time,
    )

    return {"detail": "Sessão finalizada com sucesso."}
