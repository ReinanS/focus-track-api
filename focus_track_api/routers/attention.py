import time

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from focus_track_api.services.attention import attention_monitor, face_mesh
from focus_track_api.services.attention_scorer import AttentionScorer
from focus_track_api.services.eye_detector import EyeDetector
from focus_track_api.services.pose_estimation import HeadPoseEstimator

router = APIRouter(
    prefix='/attention',
    tags=['attention'],
    responses={404: {'description': 'Not found'}},
)


@router.websocket('/monitor')
async def monitor(websocket: WebSocket):
    await websocket.accept()

    try:
        if not cv2.useOptimized():
            try:
                cv2.setUseOptimized(True)  # set OpenCV optimization to True
            except:
                print(
                    'OpenCV optimization could not be set to True, the script may be slower than expected'
                )

        face_mesh_instance = face_mesh()
        Eye_detector = EyeDetector()
        Head_pose = HeadPoseEstimator()

        # timing variables
        prev_time = time.perf_counter()
        fps = 0.0  # Initial FPS value

        t_now = time.perf_counter()

        # instantiation of the attention scorer object, with the various thresholds
        # NOTE: set verbose to True for additional printed information about the scores
        Scorer = AttentionScorer(t_now=t_now)

        while True:
            # get current time in seconds
            t_now = time.perf_counter()

            # Calculate the time taken to process the previous frame
            elapsed_time = t_now - prev_time
            prev_time = t_now

            # calculate FPS
            if elapsed_time > 0:
                fps = np.round(1 / elapsed_time, 3)

            frame_data = await websocket.receive_bytes()
            if frame_data:
                try:
                    data = attention_monitor(
                        frame_data,
                        face_mesh_instance,
                        t_now,
                        fps,
                        Eye_detector,
                        Head_pose,
                        Scorer,
                    )
                    await websocket.send_json(data)
                except Exception as e:
                    print(f'Erro ao processar frame: {e}')
                    await websocket.send_json({'error': str(e)})
    except WebSocketDisconnect:
        print('Cliente desconectado.')
