from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.models import DailySummary, StudySession, User
from focus_track_api.schemas.daily_summary import DailySummaryCreate


async def get_or_create_daily_summary(
    session: AsyncSession, summary_data: DailySummaryCreate
) -> DailySummary:
    stmt = select(DailySummary).where(
        (DailySummary.user_id == summary_data.user_id)
        & (
            func.date(DailySummary.created_at)
            == summary_data.created_at.date()
        )
    )

    daily_summary = await session.scalar(stmt)

    if daily_summary:
        return daily_summary

    # Criar se não existir
    new_summary = DailySummary(
        **summary_data.model_dump(exclude={'created_at'})
    )
    session.add(new_summary)
    await session.commit()
    await session.refresh(new_summary)

    return new_summary


async def update_daily_summary_from_sessions(
    session: AsyncSession, daily_summary: DailySummary
) -> DailySummary:
    """Atualiza o resumo diário com base nas sessões de estudo"""

    print(f'DEBUG - Atualizando DailySummary ID: {daily_summary.id}')

    # Buscar todas as sessões do resumo diário
    stmt = select(StudySession).where(
        StudySession.daily_summary_id == daily_summary.id
    )
    result = await session.execute(stmt)
    study_sessions = result.scalars().all()

    print(f'DEBUG - Encontradas {len(study_sessions)} sessões')

    if not study_sessions:
        return daily_summary

    # Calcular métricas agregadas
    total_fatigue = 0
    total_distraction = 0
    total_focused_time = 0
    session_count = 0

    for study_session in study_sessions:
        print(
            f'DEBUG - Sessão {study_session.id}: fatigue={study_session.average_fatigue}, distraction={study_session.average_distraction}'
        )

        # Calcular tempo focado (duração efetiva em milissegundos)
        if study_session.start_time and study_session.end_time:
            duration_seconds = (
                study_session.end_time - study_session.start_time
            ).total_seconds()
            # Subtrair tempo pausado
            effective_duration = (
                duration_seconds - study_session.total_paused_time
            )

            print(f'DEBUG - Duração efetiva: {effective_duration} segundos')

            # Só contar sessões com duração efetiva positiva
            if effective_duration > 0:
                total_focused_time += (
                    effective_duration * 1000
                )  # Converter para milissegundos

                # Adicionar dados de fadiga e distração (incluir mesmo valores zero)
                total_fatigue += study_session.average_fatigue
                total_distraction += study_session.average_distraction
                session_count += 1

                print(
                    f'DEBUG - Adicionado: fatigue={study_session.average_fatigue}, distraction={study_session.average_distraction}'
                )

    print(
        f'DEBUG - Total: fatigue={total_fatigue}, distraction={total_distraction}, sessions={session_count}'
    )

    if session_count > 0:
        # Calcular médias
        daily_summary.avg_fatigue = total_fatigue / session_count
        daily_summary.avg_distraction = total_distraction / session_count
        daily_summary.focused_time = int(total_focused_time)

        print(
            f'DEBUG - Médias calculadas: avg_fatigue={daily_summary.avg_fatigue}, avg_distraction={daily_summary.avg_distraction}, focused_time={daily_summary.focused_time}'
        )

    await session.commit()
    await session.refresh(daily_summary)

    return daily_summary


async def update_all_daily_summaries(
    session: AsyncSession, user: User
) -> list[DailySummary]:
    """Atualiza todos os resumos diários do usuário"""

    # Buscar todos os resumos diários do usuário
    stmt = select(DailySummary).where(DailySummary.user_id == user.id)
    result = await session.execute(stmt)
    daily_summaries = result.scalars().all()

    updated_summaries = []
    for daily_summary in daily_summaries:
        updated_summary = await update_daily_summary_from_sessions(
            session, daily_summary
        )
        updated_summaries.append(updated_summary)

    return updated_summaries


async def get_daily_and_session_data(
    session: AsyncSession, user: User
) -> tuple[list[DailySummary], list[StudySession]]:
    # Consulta todas as summaries e sessions do usuário
    daily_stmt = (
        select(DailySummary)
        .where(DailySummary.user_id == user.id)
        .order_by(DailySummary.created_at.desc())
    )
    session_stmt = (
        select(StudySession)
        .where(StudySession.user_id == user.id)
        .order_by(StudySession.created_at.desc())
    )

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
        setattr(ds, 'breaks', summary_id_to_count.get(ds.id, 0))

    return daily_summaries, study_sessions
