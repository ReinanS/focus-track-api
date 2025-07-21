from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.models import DailySummary, StudySession, User
from focus_track_api.schemas.daily_summary import DailySummaryCreate


async def get_or_create_daily_summary(
    session: AsyncSession,
    summary_data: DailySummaryCreate
) -> DailySummary:
    stmt = select(DailySummary).where(
        (DailySummary.user_id == summary_data.user_id)
        & (DailySummary.date == summary_data.date)
    )

    daily_summary = await session.scalar(stmt)

    if daily_summary:
        return daily_summary

    # Criar se não existir
    new_summary = DailySummary(**summary_data.model_dump())
    session.add(new_summary)
    await session.commit()
    await session.refresh(new_summary)

    return new_summary


async def get_daily_and_session_data(
    session: AsyncSession,
    user: User
) -> tuple[list[DailySummary], list[StudySession]]:
    # Consulta todas as summaries e sessions do usuário
    daily_stmt = select(DailySummary).where(DailySummary.user_id == user.id)
    session_stmt = select(StudySession).where(StudySession.user_id == user.id)

    daily_result = await session.execute(daily_stmt)
    session_result = await session.execute(session_stmt)

    daily_summaries = daily_result.scalars().all()
    study_sessions = session_result.scalars().all()

    # Conta quantas sessions existem por summary
    summary_id_to_count = defaultdict(int)
    for s in study_sessions:
        summary_id_to_count[s.daily_summary_id] += 1

    # Adiciona o campo `breaks` dinamicamente a cada summary
    for ds in daily_summaries:
        setattr(ds, "breaks", summary_id_to_count.get(ds.id, 0))

    return daily_summaries, study_sessions
