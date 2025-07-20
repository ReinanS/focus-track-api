from collections import defaultdict
from uuid import UUID

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


async def update_daily_summary_metrics(
    daily_summary_id: UUID,
    session: AsyncSession,
):
    stmt = select(StudySession).where(StudySession.daily_summary_id == daily_summary_id)
    result = await session.execute(stmt)
    sessions = result.scalars().all()

    if not sessions:
        return

    avg_fatigue = sum(s.average_fatigue for s in sessions) / len(sessions)
    avg_distraction = sum(s.average_distraction for s in sessions) / len(sessions)
    total_focused_minutes = sum(s.duration_minutes for s in sessions)

    stmt_summary = select(DailySummary).where(DailySummary.id == daily_summary_id)
    summary = await session.scalar(stmt_summary)

    if summary:
        summary.avg_fatigue = round(avg_fatigue, 2)
        summary.avg_distraction = round(avg_distraction, 2)
        summary.focused_time_minutes = total_focused_minutes

        await session.commit()
        await session.refresh(summary)


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
