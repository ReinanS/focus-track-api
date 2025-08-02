from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from focus_track_api.schemas.user_settings import (
    UserSettingsUpdate,
)
from focus_track_api.services.user_settings import (
    get_user_settings,
    update_user_settings,
)
from tests.factories import UserFactory, UserSettingsFactory

# Constantes para valores de teste
DEFAULT_FATIGUE_THRESHOLD = 70
DEFAULT_DISTRACTION_THRESHOLD = 60
CUSTOM_FATIGUE_THRESHOLD = 65
CUSTOM_DISTRACTION_THRESHOLD = 55
UPDATED_FATIGUE_THRESHOLD = 75
UPDATED_DISTRACTION_THRESHOLD = 65
PARTIAL_FATIGUE_THRESHOLD = 80
PARTIAL_DISTRACTION_THRESHOLD = 40
DEFAULT_UPDATE_FATIGUE_THRESHOLD = 60
DEFAULT_UPDATE_DISTRACTION_THRESHOLD = 50


@pytest.mark.asyncio
async def test_get_user_settings_exists(session):
    """Testa busca de user settings existente"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    settings = UserSettingsFactory(
        user=user,
        fatigue_threshold=CUSTOM_FATIGUE_THRESHOLD,
        distraction_threshold=CUSTOM_DISTRACTION_THRESHOLD,
    )
    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    result = await get_user_settings(user.id, session)

    assert result is not None
    assert result.user_id == user.id
    assert result.fatigue_threshold == CUSTOM_FATIGUE_THRESHOLD
    assert result.distraction_threshold == CUSTOM_DISTRACTION_THRESHOLD


@pytest.mark.asyncio
async def test_get_user_settings_not_exists(session):
    """Testa busca de user settings inexistente"""
    non_existent_user_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await get_user_settings(non_existent_user_id, session)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert 'User settings not found' in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_user_settings_success(session):
    """Testa atualização bem-sucedida de user settings"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    settings = UserSettingsFactory(
        user=user,
        fatigue_threshold=CUSTOM_FATIGUE_THRESHOLD,
        distraction_threshold=CUSTOM_DISTRACTION_THRESHOLD,
    )
    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    update_data = UserSettingsUpdate(
        fatigue_threshold=UPDATED_FATIGUE_THRESHOLD,
        distraction_threshold=UPDATED_DISTRACTION_THRESHOLD,
    )

    result = await update_user_settings(user.id, update_data, session)

    assert result is not None
    assert result.user_id == user.id
    assert result.fatigue_threshold == UPDATED_FATIGUE_THRESHOLD
    assert result.distraction_threshold == UPDATED_DISTRACTION_THRESHOLD


@pytest.mark.asyncio
async def test_update_user_settings_partial(session):
    """Testa atualização parcial de user settings"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    settings = UserSettingsFactory(
        user=user,
        fatigue_threshold=CUSTOM_FATIGUE_THRESHOLD,
        distraction_threshold=CUSTOM_DISTRACTION_THRESHOLD,
    )
    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    # Atualizar apenas fatigue_threshold
    update_data = UserSettingsUpdate(
        fatigue_threshold=PARTIAL_FATIGUE_THRESHOLD
    )

    result = await update_user_settings(user.id, update_data, session)

    assert result is not None
    assert result.fatigue_threshold == PARTIAL_FATIGUE_THRESHOLD
    assert (
        result.distraction_threshold == CUSTOM_DISTRACTION_THRESHOLD
    )  # Mantém valor original


@pytest.mark.asyncio
async def test_update_user_settings_not_exists(session):
    """Testa atualização de user settings inexistente"""
    non_existent_user_id = uuid4()
    update_data = UserSettingsUpdate(
        fatigue_threshold=UPDATED_FATIGUE_THRESHOLD
    )

    with pytest.raises(HTTPException) as exc_info:
        await update_user_settings(non_existent_user_id, update_data, session)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert 'User settings not found' in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_user_settings_with_defaults(session):
    """Testa atualização com valores padrão"""
    user = UserFactory()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    settings = UserSettingsFactory(
        user=user,
        fatigue_threshold=CUSTOM_FATIGUE_THRESHOLD,
        distraction_threshold=CUSTOM_DISTRACTION_THRESHOLD,
    )
    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    # Atualizar com valores padrão
    update_data = UserSettingsUpdate()

    result = await update_user_settings(user.id, update_data, session)

    assert result is not None
    assert result.fatigue_threshold == CUSTOM_FATIGUE_THRESHOLD  # Mantém valor original
    assert result.distraction_threshold == CUSTOM_DISTRACTION_THRESHOLD  # Mantém valor original
