import pytest
from fastapi import status

from tests.factories import UserSettingsFactory

# Constantes para valores de teste
DEFAULT_FATIGUE_THRESHOLD = 70
DEFAULT_DISTRACTION_THRESHOLD = 60
CUSTOM_FATIGUE_THRESHOLD = 75
CUSTOM_DISTRACTION_THRESHOLD = 65
PARTIAL_FATIGUE_THRESHOLD = 80
PARTIAL_DISTRACTION_THRESHOLD = 40
EXPECTED_HTTP_OK = 200


@pytest.mark.asyncio
async def test_read_settings_success(client, session, user, token):
    """Testa leitura bem-sucedida de user settings"""
    # Criar settings para o usuário
    settings = UserSettingsFactory(
        user=user,
        fatigue_threshold=DEFAULT_FATIGUE_THRESHOLD,
        distraction_threshold=DEFAULT_DISTRACTION_THRESHOLD,
    )
    session.add(settings)
    await session.commit()

    response = client.get(
        '/settings/', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['user_id'] == str(user.id)
    assert data['fatigue_threshold'] == DEFAULT_FATIGUE_THRESHOLD
    assert data['distraction_threshold'] == DEFAULT_DISTRACTION_THRESHOLD


def test_read_settings_not_found(client, session, user, token):
    """Testa leitura quando settings não existem"""
    response = client.get(
        '/settings/', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'User settings not found' in response.json()['detail']


def test_read_settings_unauthorized(client):
    """Testa leitura sem autenticação"""
    response = client.get('/settings/')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_settings_success(client, session, user, token):
    """Testa atualização bem-sucedida de user settings"""
    # Criar settings para o usuário
    settings = UserSettingsFactory(
        user=user,
        fatigue_threshold=DEFAULT_FATIGUE_THRESHOLD,
        distraction_threshold=DEFAULT_DISTRACTION_THRESHOLD,
    )
    session.add(settings)
    await session.commit()

    update_data = {
        'fatigue_threshold': CUSTOM_FATIGUE_THRESHOLD,
        'distraction_threshold': CUSTOM_DISTRACTION_THRESHOLD,
    }

    response = client.put(
        '/settings/',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == EXPECTED_HTTP_OK
    data = response.json()
    assert data['user_id'] == str(user.id)
    assert data['fatigue_threshold'] == CUSTOM_FATIGUE_THRESHOLD
    assert data['distraction_threshold'] == CUSTOM_DISTRACTION_THRESHOLD


@pytest.mark.asyncio
async def test_update_settings_partial(client, session, user, token):
    """Testa atualização parcial de user settings"""
    # Criar settings para o usuário
    settings = UserSettingsFactory(
        user=user,
        fatigue_threshold=DEFAULT_FATIGUE_THRESHOLD,
        distraction_threshold=PARTIAL_DISTRACTION_THRESHOLD,
    )
    session.add(settings)
    await session.commit()

    # Atualizar apenas fatigue_threshold
    update_data = {'fatigue_threshold': PARTIAL_FATIGUE_THRESHOLD}

    response = client.put(
        '/settings/',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['fatigue_threshold'] == PARTIAL_FATIGUE_THRESHOLD
    assert (
        data['distraction_threshold'] == PARTIAL_DISTRACTION_THRESHOLD
    )  # Mantém valor original


def test_update_settings_not_found(client, session, user, token):
    """Testa atualização quando settings não existem"""
    update_data = {'fatigue_threshold': CUSTOM_FATIGUE_THRESHOLD}

    response = client.put(
        '/settings/',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'User settings not found' in response.json()['detail']


def test_update_settings_unauthorized(client):
    """Testa atualização sem autenticação"""
    update_data = {'fatigue_threshold': CUSTOM_FATIGUE_THRESHOLD}

    response = client.put('/settings/', json=update_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_settings_invalid_data(client, session, user, token):
    """Testa atualização com dados inválidos"""
    # Criar settings para o usuário
    settings = UserSettingsFactory(
        user=user,
        fatigue_threshold=DEFAULT_FATIGUE_THRESHOLD,
        distraction_threshold=DEFAULT_DISTRACTION_THRESHOLD,
    )
    session.add(settings)
    await session.commit()

    # Dados inválidos (valores negativos)
    update_data = {'fatigue_threshold': -10, 'distraction_threshold': -5}

    response = client.put(
        '/settings/',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
