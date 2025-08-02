from datetime import datetime, timezone
from uuid import uuid4

import pytest

from focus_track_api.schemas.study_session import StudySessionCreate
from focus_track_api.services.study_session import (
    create_study_session,
    end_study_session,
    get_study_session,
)
from tests.factories import (
    DailySummaryFactory,
    StudySessionFactory,
    UserFactory,
)

# Constantes para valores de teste
EXPECTED_ATTENTION_SCORE = 85.5
EXPECTED_FATIGUE_SCORE = 15.2
EXPECTED_DISTRACTION_SCORE = 10.3
EXPECTED_DISTRACTION_RATE = 8.5
EXPECTED_MAX_FATIGUE = 25.0
EXPECTED_MAX_DISTRACTION = 20.0
EXPECTED_PERCLOS = 12.5


@pytest.mark.asyncio
async def test_create_study_session_success(session):
    """Testa criação bem-sucedida de study session"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    session_data = StudySessionCreate(
        user_id=user.id, start_time=datetime.now(timezone.utc)
    )

    result = await create_study_session(session, session_data)

    assert result is not None
    assert result.user_id == user.id
    assert result.start_time is not None
    assert result.average_attention_score == 0.0
    assert result.average_fatigue == 0.0
    assert result.average_distraction == 0.0
    assert result.daily_summary_id is not None


@pytest.mark.asyncio
async def test_create_study_session_with_custom_start_time(session):
    """Testa criação com start_time customizado"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    custom_start_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    session_data = StudySessionCreate(
        user_id=user.id, start_time=custom_start_time
    )

    result = await create_study_session(session, session_data)

    # Comparar apenas a data e hora, ignorando timezone
    assert result.start_time.replace(tzinfo=None) == custom_start_time.replace(
        tzinfo=None
    )


@pytest.mark.asyncio
async def test_get_study_session_exists(session):
    """Testa busca de study session existente"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Criar primeiro um DailySummary
    daily_summary = DailySummaryFactory(user_id=user.id)
    session.add(daily_summary)
    await session.commit()
    await session.refresh(daily_summary)

    # Criar StudySession com o daily_summary_id correto
    study_session = StudySessionFactory(
        user_id=user.id, daily_summary_id=daily_summary.id
    )
    session.add(study_session)
    await session.commit()
    await session.refresh(study_session)

    result = await get_study_session(session, study_session.id)

    assert result is not None
    assert result.id == study_session.id
    assert result.user_id == user.id


@pytest.mark.asyncio
async def test_get_study_session_not_exists(session):
    """Testa busca de study session inexistente"""
    non_existent_id = uuid4()
    result = await get_study_session(session, non_existent_id)

    assert result is None


@pytest.mark.asyncio
async def test_end_study_session_success(session):
    """Testa finalização bem-sucedida de study session"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Criar primeiro um DailySummary
    daily_summary = DailySummaryFactory(user_id=user.id)
    session.add(daily_summary)
    await session.commit()
    await session.refresh(daily_summary)

    study_session = StudySessionFactory(
        user_id=user.id, daily_summary_id=daily_summary.id
    )
    session.add(study_session)
    await session.commit()
    await session.refresh(study_session)

    # Dados para atualização
    update_data = StudySessionCreate(
        user_id=user.id,
        daily_summary_id=daily_summary.id,
        start_time=study_session.start_time,
        average_attention_score=EXPECTED_ATTENTION_SCORE,
        average_fatigue=EXPECTED_FATIGUE_SCORE,
        average_distraction=EXPECTED_DISTRACTION_SCORE,
        distraction_rate=EXPECTED_DISTRACTION_RATE,
        max_fatigue=EXPECTED_MAX_FATIGUE,
        max_distraction=EXPECTED_MAX_DISTRACTION,
        perclos=EXPECTED_PERCLOS,
    )

    result = await end_study_session(study_session.id, update_data, session)

    assert result is not None
    assert result.id == study_session.id
    assert result.end_time is not None
    assert result.average_attention_score == EXPECTED_ATTENTION_SCORE
    assert result.average_fatigue == EXPECTED_FATIGUE_SCORE
    assert result.average_distraction == EXPECTED_DISTRACTION_SCORE
    assert result.distraction_rate == EXPECTED_DISTRACTION_RATE
    assert result.max_fatigue == EXPECTED_MAX_FATIGUE
    assert result.max_distraction == EXPECTED_MAX_DISTRACTION
    assert result.perclos == EXPECTED_PERCLOS


@pytest.mark.asyncio
async def test_end_study_session_not_found(session):
    """Testa finalização de study session inexistente"""
    non_existent_id = uuid4()
    update_data = StudySessionCreate(
        user_id=uuid4(), start_time=datetime.now(timezone.utc)
    )

    with pytest.raises(
        ValueError, match=f'StudySession with id {non_existent_id} not found'
    ):
        await end_study_session(non_existent_id, update_data, session)


@pytest.mark.asyncio
async def test_end_study_session_without_end_time(session):
    """Testa finalização sem end_time (deve usar o existente)"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Criar primeiro um DailySummary
    daily_summary = DailySummaryFactory(user_id=user.id)
    session.add(daily_summary)
    await session.commit()
    await session.refresh(daily_summary)

    study_session = StudySessionFactory(
        user_id=user.id, daily_summary_id=daily_summary.id
    )
    session.add(study_session)
    await session.commit()
    await session.refresh(study_session)

    # Dados para atualização sem end_time
    update_data = StudySessionCreate(
        user_id=user.id,
        daily_summary_id=daily_summary.id,
        start_time=study_session.start_time,
        average_attention_score=EXPECTED_ATTENTION_SCORE,
    )

    result = await end_study_session(study_session.id, update_data, session)

    assert result is not None
    assert result.average_attention_score == EXPECTED_ATTENTION_SCORE
    # end_time deve ser preenchido ao finalizar a sessão
    assert result.end_time is not None
