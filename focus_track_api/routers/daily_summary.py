from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.database import get_session
from focus_track_api.models import DailySummary, User
from focus_track_api.schemas.daily_summary import (
    DailyAndSessionResponse,
    DailySummarySchema,
)
from focus_track_api.security import get_current_user
from focus_track_api.services.daily_summary import (
    get_daily_and_session_data,
    update_all_daily_summaries,
)

router = APIRouter(prefix='/daily-summary', tags=['daily-summary'])

Session = Depends(get_session)
CurrentUser = Depends(get_current_user)


@router.get('/', response_model=list[DailySummarySchema])
async def list_daily_summaries(
    session: AsyncSession = Session,
    current_user: User = CurrentUser,
):
    result = await session.execute(
        select(DailySummary).where(DailySummary.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get('/overview', response_model=DailyAndSessionResponse)
async def get_overview_data(
    session: AsyncSession = Session,
    current_user: User = CurrentUser,
):
    daily_summaries, study_sessions = await get_daily_and_session_data(
        session, current_user
    )

    return DailyAndSessionResponse(
        daily_data=daily_summaries, session_data=study_sessions
    )


@router.post('/update-all', response_model=list[DailySummarySchema])
async def update_all_summaries(
    session: AsyncSession = Session,
    current_user: User = CurrentUser,
):
    """Atualiza todos os resumos diários do usuário com base nas sessões existentes"""
    updated_summaries = await update_all_daily_summaries(session, current_user)
    return updated_summaries
