import time
from datetime import datetime, timezone

import pytest

from focus_track_api.schemas.daily_summary import DailySummaryCreate
from focus_track_api.services.daily_summary import (
    get_daily_and_session_data,
    get_or_create_daily_summary,
)
from tests.factories import (
    DailySummaryFactory,
    StudySessionFactory,
    UserFactory,
)

# Constantes para valores de teste
EXPECTED_DAILY_SUMMARIES_COUNT = 2
EXPECTED_STUDY_SESSIONS_COUNT = 3
EXPECTED_BREAKS_FOR_TWO_SESSIONS = 2
EXPECTED_BREAKS_FOR_ONE_SESSION = 1


@pytest.mark.asyncio
async def test_get_or_create_daily_summary_creates_new(session):
    """Testa criação de novo daily summary"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    summary_data = DailySummaryCreate(
        user_id=user.id, created_at=datetime.now(timezone.utc)
    )

    result = await get_or_create_daily_summary(session, summary_data)

    assert result is not None
    assert result.user_id == user.id
    assert result.avg_fatigue == 0.0
    assert result.avg_distraction == 0.0
    assert result.focused_time == 0


@pytest.mark.asyncio
async def test_get_or_create_daily_summary_returns_existing(session):
    """Testa retorno de daily summary existente"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Criar summary existente
    existing_summary = DailySummaryFactory(user_id=user.id)
    session.add(existing_summary)
    await session.commit()
    await session.refresh(existing_summary)

    summary_data = DailySummaryCreate(
        user_id=user.id, created_at=datetime.now(timezone.utc)
    )

    result = await get_or_create_daily_summary(session, summary_data)

    assert result is not None
    assert result.id == existing_summary.id
    assert result.user_id == user.id


@pytest.mark.asyncio
async def test_get_daily_and_session_data_returns_correct_data(session):
    """Testa retorno correto de dados de daily summary e sessions"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Criar daily summaries
    summary1 = DailySummaryFactory(user_id=user.id)
    summary2 = DailySummaryFactory(user_id=user.id)
    session.add_all([summary1, summary2])
    await session.commit()

    # Criar study sessions
    session1 = StudySessionFactory(
        user_id=user.id, daily_summary_id=summary1.id
    )
    session2 = StudySessionFactory(
        user_id=user.id, daily_summary_id=summary1.id
    )
    session3 = StudySessionFactory(
        user_id=user.id, daily_summary_id=summary2.id
    )
    session.add_all([session1, session2, session3])
    await session.commit()

    daily_summaries, study_sessions = await get_daily_and_session_data(
        session, user
    )

    assert len(daily_summaries) == EXPECTED_DAILY_SUMMARIES_COUNT
    assert len(study_sessions) == EXPECTED_STUDY_SESSIONS_COUNT

    # Verificar se o campo breaks foi adicionado
    for summary in daily_summaries:
        assert hasattr(summary, 'breaks')

    # Verificar contagem correta de breaks
    summary1_with_breaks = next(
        s for s in daily_summaries if s.id == summary1.id
    )
    summary2_with_breaks = next(
        s for s in daily_summaries if s.id == summary2.id
    )

    assert (
        summary1_with_breaks.breaks == EXPECTED_BREAKS_FOR_TWO_SESSIONS
    )  # 2 sessions
    assert (
        summary2_with_breaks.breaks == EXPECTED_BREAKS_FOR_ONE_SESSION
    )  # 1 session


@pytest.mark.asyncio
async def test_get_daily_and_session_data_empty_user(session):
    """Testa retorno para usuário sem dados"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    daily_summaries, study_sessions = await get_daily_and_session_data(
        session, user
    )

    assert len(daily_summaries) == 0
    assert len(study_sessions) == 0


@pytest.mark.asyncio
async def test_get_daily_and_session_data_orders_by_created_at_desc(session):
    """Testa ordenação por created_at desc"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Criar summaries com datas diferentes
    summary1 = DailySummaryFactory(user_id=user.id)
    session.add(summary1)
    await session.commit()

    # Aguardar um pouco para garantir diferença de timestamp
    time.sleep(0.1)

    summary2 = DailySummaryFactory(user_id=user.id)
    session.add(summary2)
    await session.commit()

    daily_summaries, _ = await get_daily_and_session_data(session, user)

    assert len(daily_summaries) == EXPECTED_DAILY_SUMMARIES_COUNT
    assert daily_summaries[0].created_at > daily_summaries[1].created_at
