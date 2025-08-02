import pytest
from fastapi import status

from tests.factories import (
    DailySummaryFactory,
    StudySessionFactory,
)

# Constantes para valores de teste
EXPECTED_DAILY_SUMMARIES_COUNT = 2
EXPECTED_STUDY_SESSIONS_COUNT = 3


@pytest.mark.asyncio
async def test_list_daily_summaries_success(client, session, user, token):
    """Testa listagem bem-sucedida de daily summaries"""
    # Criar daily summaries para o usuário
    summary1 = DailySummaryFactory(user_id=user.id)
    summary2 = DailySummaryFactory(user_id=user.id)
    session.add_all([summary1, summary2])
    await session.commit()

    response = client.get(
        '/daily-summary/', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == EXPECTED_DAILY_SUMMARIES_COUNT
    assert all(summary['user_id'] == str(user.id) for summary in data)


@pytest.mark.asyncio
async def test_list_daily_summaries_empty(client, session, user, token):
    """Testa listagem quando não há daily summaries"""
    response = client.get(
        '/daily-summary/', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0


def test_list_daily_summaries_unauthorized(client):
    """Testa listagem sem autenticação"""
    response = client.get('/daily-summary/')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_overview_data_success(client, session, user, token):
    """Testa obtenção de dados de overview"""
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

    response = client.get(
        '/daily-summary/overview', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert 'daily_data' in data
    assert 'session_data' in data
    assert len(data['daily_data']) == EXPECTED_DAILY_SUMMARIES_COUNT
    assert len(data['session_data']) == EXPECTED_STUDY_SESSIONS_COUNT

    # Verificar se o campo breaks foi adicionado
    for summary in data['daily_data']:
        assert 'breaks' in summary


@pytest.mark.asyncio
async def test_get_overview_data_empty(client, session, user, token):
    """Testa obtenção de dados de overview quando vazio"""
    response = client.get(
        '/daily-summary/overview', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert 'daily_data' in data
    assert 'session_data' in data
    assert len(data['daily_data']) == 0
    assert len(data['session_data']) == 0


def test_get_overview_data_unauthorized(client):
    """Testa obtenção de dados de overview sem autenticação"""
    response = client.get('/daily-summary/overview')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
