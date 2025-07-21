from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.models import StudySession
from focus_track_api.schemas.daily_summary import DailySummaryCreate
from focus_track_api.schemas.study_session import StudySessionCreate
from focus_track_api.services.daily_summary import get_or_create_daily_summary


async def create_study_session(
    session: AsyncSession, session_data: StudySessionCreate
) -> StudySession:
    new_session = StudySession(**session_data.model_dump())
    daily_summary = await get_or_create_daily_summary(
        session=session,
        summary_data=DailySummaryCreate(
            user_id=session_data.user_id,
            date=datetime.now(tz=ZoneInfo('UTC')).date(),
        ),
    )

    new_session.daily_summary = daily_summary
    session.add(new_session)

    try:
        await session.commit()
        await session.refresh(new_session)
        return new_session
    except SQLAlchemyError as e:
        await session.rollback()
        raise RuntimeError(f"Erro ao salvar StudySession: {e}")


async def end_study_session(
    study_session_id: UUID,
    update_data: StudySessionCreate,
    session: AsyncSession
) -> StudySession:
    stmt = select(StudySession).where(StudySession.id == study_session_id)
    result = await session.execute(stmt)
    db_session = result.scalar_one_or_none()

    if db_session is None:
        raise ValueError(f"StudySession with id {study_session_id} not found.")

    # Atualiza os campos finais
    db_session.average_attention_score = update_data.average_attention_score
    db_session.average_fatigue = update_data.average_fatigue
    db_session.average_distraction = update_data.average_distraction
    db_session.distraction_rate = update_data.distraction_rate
    db_session.max_fatigue = update_data.max_fatigue
    db_session.max_distraction = update_data.max_distraction
    db_session.perclos = update_data.perclos

    await session.commit()
    await session.refresh(db_session)

    return db_session


async def get_study_session(
    session: AsyncSession,
    session_id: UUID
) -> StudySession:
    stmt = select(StudySession).where(StudySession.id == session_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
