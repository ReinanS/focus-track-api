import time
from datetime import datetime
from fastapi.params import Depends
from typing_extensions import Annotated

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.database import get_session
from focus_track_api.models import User
from focus_track_api.schemas.session_metrics import SessionMetrics
from focus_track_api.security import get_current_user
from focus_track_api.services.attention import (
    finalize_session,
    handle_frame,
    init_cv_dependencies,
    start_study_session,
)
from focus_track_api.services.attention_scorer import AttentionScorer

router = APIRouter(
    prefix='/attention',
    tags=['attention'],
    responses={404: {'description': 'Not found'}},
)

@router.websocket("/monitor")
async def monitor_session(
    websocket: WebSocket,
):
    await websocket.accept()
    print("WebSocket connection established")
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Token is required")
        return
    # user = await get_current_user(token=token)
    # print('user', user)
    # session = get_session()

    face_mesh_instance, eye_detector, head_pose = init_cv_dependencies()

    metrics = SessionMetrics()
    scorer = AttentionScorer(t_now := time.perf_counter())
    start_time = datetime.now()
    prev_time = t_now
    fps = 0.0
    # studySession = await start_study_session(session, user)

    try:
        while True:
            t_now = time.perf_counter()
            elapsed_time = t_now - prev_time
            prev_time = t_now

            if elapsed_time > 0:
                fps = round(1 / elapsed_time, 3)

            frame_data = await websocket.receive_bytes()
            if frame_data:
                try:
                    payload = await handle_frame(
                        frame_data, face_mesh_instance, eye_detector, t_now, fps, head_pose, scorer, metrics, start_time
                    )

                    if payload:
                        await websocket.send_json(payload.model_dump())

                except Exception as e:
                    print(f"Erro ao processar frame: {e}")
                    await websocket.send_json({"error": str(e)})
                    raise

    except WebSocketDisconnect:
        print("WebSocket disconnected")
        # await finalize_session(session, user, studySession, metrics, scorer, start_time)
        pass
