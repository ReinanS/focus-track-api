import traceback
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.models import DailySummary, StudySession
from focus_track_api.schemas.daily_summary import DailySummaryCreate
from focus_track_api.schemas.study_session import StudySessionCreate
from focus_track_api.services.daily_summary import (
    get_or_create_daily_summary,
    update_daily_summary_from_sessions,
)


async def create_study_session(
    session: AsyncSession, session_data: StudySessionCreate
) -> StudySession:
    # Criar ou obter o DailySummary primeiro
    daily_summary = await get_or_create_daily_summary(
        session=session,
        summary_data=DailySummaryCreate(
            user_id=session_data.user_id,
            created_at=datetime.now(timezone.utc),
        ),
    )

    # Filtrar apenas os campos que podem ser inicializados
    init_data = {
        key: value
        for key, value in session_data.model_dump().items()
        if hasattr(StudySession, key)
    }

    # Adicionar o daily_summary_id
    init_data['daily_summary_id'] = daily_summary.id

    study_session = StudySession(**init_data)
    session.add(study_session)
    await session.commit()
    await session.refresh(study_session)

    return study_session


async def get_study_session(
    session: AsyncSession, session_id: UUID
) -> Optional[StudySession]:
    result = await session.execute(
        select(StudySession).where(StudySession.id == session_id)
    )
    return result.scalar_one_or_none()


async def end_study_session(
    study_session_id: UUID,
    session_data: StudySessionCreate,
    session: AsyncSession,
) -> StudySession:
    stmt = select(StudySession).where(StudySession.id == study_session_id)
    result = await session.execute(stmt)
    db_session = result.scalar_one_or_none()

    if not db_session:
        raise ValueError(f'StudySession with id {study_session_id} not found')

    # Atualizar campos da sessão
    for field, value in session_data.model_dump().items():
        if hasattr(db_session, field):
            setattr(db_session, field, value)

    # Definir end_time se não estiver definido
    if not db_session.end_time:
        db_session.end_time = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(db_session)

    try:
        # Buscar o daily_summary diretamente usando o ID
        daily_summary_stmt = select(DailySummary).where(
            DailySummary.id == db_session.daily_summary_id
        )
        daily_summary_result = await session.execute(daily_summary_stmt)
        daily_summary = daily_summary_result.scalar_one_or_none()

        if daily_summary:
            await update_daily_summary_from_sessions(session, daily_summary)
            print('DEBUG - update_daily_summary_from_sessions concluído')
        else:
            print('DEBUG - DailySummary não encontrado')

    except Exception as e:
        print(f'DEBUG - Erro em update_daily_summary_from_sessions: {e}')
        traceback.print_exc()

    return db_session
