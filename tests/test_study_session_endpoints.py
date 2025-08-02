from datetime import datetime, timezone

import pytest
from fastapi import status

from tests.factories import DailySummaryFactory, StudySessionFactory

# Constantes para valores de teste
EXPECTED_STUDY_SESSIONS_COUNT = 2


def test_create_study_session_success(client, session, user, token):
    """Testa criação bem-sucedida de study session"""
    session_data = {
        'user_id': str(user.id),
        'start_time': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(
        '/study-session/',
        json=session_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['user_id'] == str(user.id)
    assert 'start_time' in data
    assert data['average_attention_score'] == 0.0
    assert data['average_fatigue'] == 0.0
    assert data['average_distraction'] == 0.0


def test_create_study_session_unauthorized(client):
    """Testa criação sem autenticação"""
    session_data = {
        'user_id': '123e4567-e89b-12d3-a456-426614174000',
        'start_time': datetime.now(timezone.utc).isoformat(),
    }

    response = client.post('/study-session/', json=session_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_list_study_sessions_success(client, session, user, token):
    """Testa listagem bem-sucedida de study sessions"""
    # Criar primeiro um DailySummary
    daily_summary = DailySummaryFactory(user_id=user.id)
    session.add(daily_summary)
    await session.commit()
    await session.refresh(daily_summary)

    # Criar study sessions para o usuário
    session1 = StudySessionFactory(
        user_id=user.id, daily_summary_id=daily_summary.id
    )
    session2 = StudySessionFactory(
        user_id=user.id, daily_summary_id=daily_summary.id
    )
    session.add_all([session1, session2])
    await session.commit()

    response = client.get(
        '/study-session/', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == EXPECTED_STUDY_SESSIONS_COUNT
    assert all(session['user_id'] == str(user.id) for session in data)


@pytest.mark.asyncio
async def test_list_study_sessions_empty(client, session, user, token):
    """Testa listagem quando não há study sessions"""
    response = client.get(
        '/study-session/', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0


def test_list_study_sessions_unauthorized(client):
    """Testa listagem sem autenticação"""
    response = client.get('/study-session/')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_study_session_success(client, session, user, token):
    """Testa obtenção bem-sucedida de study session específica"""
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

    response = client.get(
        f'/study-session/{study_session.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == str(study_session.id)
    assert data['user_id'] == str(user.id)


def test_get_study_session_not_found(client, session, user, token):
    """Testa obtenção de study session inexistente"""
    non_existent_id = '123e4567-e89b-12d3-a456-426614174000'
    response = client.get(
        f'/study-session/{non_existent_id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'Sessão de estudo não encontrada' in response.json()['detail']


def test_get_study_session_invalid_id(client, session, user, token):
    """Testa obtenção com ID inválido"""
    response = client.get(
        '/study-session/invalid-id',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'ID inválido' in response.json()['detail']


def test_get_study_session_unauthorized(client):
    """Testa obtenção sem autenticação"""
    response = client.get(
        '/study-session/123e4567-e89b-12d3-a456-426614174000'
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_start_study_session_success(client, session, user, token):
    """Testa início bem-sucedido de study session"""
    response = client.post(
        '/study-session/start', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['user_id'] == str(user.id)
    assert 'start_time' in data
    assert data['average_attention_score'] == 0.0
    assert data['average_fatigue'] == 0.0
    assert data['average_distraction'] == 0.0


def test_start_study_session_unauthorized(client):
    """Testa início sem autenticação"""
    response = client.post('/study-session/start')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_finalize_study_session_success(client, session, user, token):
    """Testa finalização bem-sucedida de study session"""
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

    response = client.post(
        f'/study-session/finalize/{study_session.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['detail'] == 'Sessão finalizada com sucesso.'


def test_finalize_study_session_not_found(client, session, user, token):
    """Testa finalização de study session inexistente"""
    non_existent_id = '123e4567-e89b-12d3-a456-426614174000'
    response = client.post(
        f'/study-session/finalize/{non_existent_id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'Sessão de estudo não encontrada' in response.json()['detail']


def test_finalize_study_session_unauthorized(client):
    """Testa finalização sem autenticação"""
    response = client.post(
        '/study-session/finalize/123e4567-e89b-12d3-a456-426614174000'
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
