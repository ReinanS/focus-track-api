import time
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.database import get_session
from focus_track_api.models import StudySession, User
from focus_track_api.schemas.session_metrics import SessionMetrics
from focus_track_api.schemas.study_session import (
    StudySessionCreate,
    StudySessionSchema,
)
from focus_track_api.security import get_current_user, get_current_user_socket
from focus_track_api.services.attention import (
    finalize_session,
    handle_frame,
    init_cv_dependencies,
    start_study_session,
)
from focus_track_api.services.attention_scorer import AttentionScorer
from focus_track_api.services.study_session import (
    create_study_session,
    get_study_session,
)

router = APIRouter(prefix='/study-session', tags=['study-session'])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _process_frame_payload(payload):
    """Processa o payload do frame e retorna o formato adequado para envio"""
    if isinstance(payload, dict) and 'error' in payload:
        return payload
    elif isinstance(payload, dict):
        # Se é um dicionário (com informações de status da sessão)
        return payload
    else:
        # Se é um objeto Pydantic (FrameMetrics)
        return payload.model_dump()


async def _handle_frame_processing(
    frame_data: bytes,
    face_mesh_instance,
    eye_detector,
    t_now: float,
    fps: float,
    head_pose,
    scorer,
    metrics,
    start_time,
    study_session,
    session,
):
    """Processa um frame e retorna o payload"""
    payload = await handle_frame(
        frame_data,
        face_mesh_instance,
        eye_detector,
        t_now,
        fps,
        head_pose,
        scorer,
        metrics,
        start_time,
        study_session,
        session,
    )
    return _process_frame_payload(payload)


@router.websocket('/monitor')
async def monitor_session(
    websocket: WebSocket,
):
    await websocket.accept()
    print('WebSocket connection established')
    token = websocket.query_params.get('token')
    if not token:
        await websocket.close(code=1008, reason='Token is required')
        return

    session_generator = get_session()
    session = await anext(session_generator)
    user = await get_current_user_socket(session, token=token)

    face_mesh_instance, eye_detector, head_pose = init_cv_dependencies()

    metrics = SessionMetrics()
    scorer = AttentionScorer(t_now := time.perf_counter())
    studySession = await start_study_session(session, user)
    start_time = studySession.start_time  # Usar o start_time da sessão criada
    prev_time = t_now
    fps = 0.0

    try:
        while True:
            t_now = time.perf_counter()
            elapsed_time = t_now - prev_time
            prev_time = t_now

            if elapsed_time > 0:
                fps = round(1 / elapsed_time, 3)

            frame_data = await websocket.receive_bytes()
            if not frame_data:
                continue

            try:
                payload = await _handle_frame_processing(
                    frame_data,
                    face_mesh_instance,
                    eye_detector,
                    t_now,
                    fps,
                    head_pose,
                    scorer,
                    metrics,
                    start_time,
                    studySession,
                    session,
                )
                await websocket.send_json(payload)

            except Exception as e:
                print(f'Erro ao processar frame: {e}')
                error_payload = {
                    'error': 'WEBSOCKET_ERROR',
                    'message': f'Erro na conexão WebSocket: {str(e)}',
                    'type': 'WEBSOCKET',
                }
                await websocket.send_json(error_payload)
                raise

    except WebSocketDisconnect:
        print('WebSocket disconnected')
        await finalize_session(session, user, studySession, metrics, scorer)

        # Tentar enviar mensagem de finalização antes de fechar
        try:
            finalization_message = {
                'session_status': 'finished',
                'total_paused_time': studySession.total_paused_time,
                'paused_at': None,
                'message': 'Sessão finalizada com sucesso',
            }
            await websocket.send_json(finalization_message)
        except Exception:
            pass  # Ignora erro se já foi desconectado


@router.post(
    '', response_model=StudySessionSchema, status_code=HTTPStatus.CREATED
)
async def create_study_session_endpoint(
    session_data: StudySessionCreate,
    session: Session,
    current_user: CurrentUser,
):
    return await create_study_session(
        session=session,
        session_data=session_data.model_copy(
            update={'user_id': current_user.id}
        ),
    )


@router.get('', response_model=list[StudySessionSchema])
async def list_study_sessions(
    session: Session,
    current_user: CurrentUser,
):
    result = await session.execute(
        select(StudySession).where(StudySession.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get('/{session_id}', response_model=StudySessionSchema)
async def get_study_session_endpoint(
    db: Session,
    current_user: CurrentUser,
    session_id: str,
):
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail='ID inválido')

    study_session = await get_study_session(db, session_uuid)

    if not study_session or study_session.user_id != current_user.id:
        raise HTTPException(
            status_code=404, detail='Sessão de estudo não encontrada.'
        )

    return study_session


@router.post(
    '/start', response_model=StudySessionSchema, status_code=HTTPStatus.CREATED
)
async def start_study_session_endpoint(
    db: Session,
    current_user: CurrentUser,
):
    session = await start_study_session(db, current_user)
    return session


@router.post('/finalize/{session_id}', status_code=HTTPStatus.OK)
async def finalize_study_session_endpoint(
    session_id: str,
    db: Session,
    current_user: CurrentUser,
):
    study_session = await get_study_session(db, UUID(session_id))

    if not study_session:
        raise HTTPException(
            status_code=404, detail='Sessão de estudo não encontrada.'
        )

    scorer = AttentionScorer(t_now=time.perf_counter())
    await finalize_session(
        session=db,
        user=current_user,
        study_session=study_session,
        metrics=SessionMetrics(),
        scorer=scorer,
    )

    return {'detail': 'Sessão finalizada com sucesso.'}
