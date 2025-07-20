import traceback
from datetime import datetime

import cv2
import mediapipe as mp
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from focus_track_api.models import StudySession, User
from focus_track_api.schemas.attention import (
    AttentionMetrics,
    FaceLandmarks,
    FrameMetrics,
    Point2D,
)
from focus_track_api.schemas.session_metrics import SessionMetrics
from focus_track_api.schemas.study_session import StudySessionCreate
from focus_track_api.services.attention_scorer import AttentionScorer
from focus_track_api.services.eye_detector import EyeDetector
from focus_track_api.services.pose_estimation import HeadPoseEstimator
from focus_track_api.services.study_session import (
    create_study_session,
    end_study_session,
)
from focus_track_api.utils.constants import (
    FACE_BOUNDARY,
    INNER_LIP,
    LEFT_EYE,
    LEFT_EYEBROW,
    LEFT_IRIS,
    NOSE,
    OUTER_LIP,
    RIGHT_EYE,
    RIGHT_EYEBROW,
    RIGHT_IRIS,
)
from focus_track_api.utils.utils import get_landmarks


def face_mesh():
    return mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        static_image_mode=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        refine_landmarks=True,
    )


def process_frame(data: bytes):
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    frame_size = img.shape[1], img.shape[0]
    gray = np.expand_dims(gray, axis=2)
    gray = np.concatenate([gray, gray, gray], axis=2)

    return gray, frame_size


def get_face_landmarks(face_mesh, frame: np.ndarray):
    width, height = frame.shape[1], frame.shape[0]
    results = face_mesh.process(frame)
    lms = results.multi_face_landmarks

    if lms:
        landmarks = get_landmarks(lms)

        # Função auxiliar para processar landmarks
        def process_landmarks(indices):
            return [
                [landmark.x * width, landmark.y * height]
                for landmark in (
                    results.multi_face_landmarks[0].landmark[i]
                    for i in indices
                )
            ]

        # Definir as regiões e seus índices
        regions = {
            'face_boundary': FACE_BOUNDARY,
            'left_eyebrow': LEFT_EYEBROW,
            'right_eyebrow': RIGHT_EYEBROW,
            'left_eye': LEFT_EYE,
            'right_eye': RIGHT_EYE,
            'left_iris': LEFT_IRIS,
            'right_iris': RIGHT_IRIS,
            'nose': NOSE,
            'inner_lips': INNER_LIP,
            'outer_lips': OUTER_LIP,
        }

        # Construir o dicionário de landmarks usando a função auxiliar
        landmarks_dict = {
            region: process_landmarks(indices)
            for region, indices in regions.items()
        }

        return landmarks_dict, landmarks

    return None


async def handle_frame(
    frame_data: bytes,
    face_mesh_instance,
    eye_detector: EyeDetector,
    t_now: float,
    fps: float,
    head_pose: HeadPoseEstimator,
    scorer: AttentionScorer,
    metrics: SessionMetrics,
    start_time: datetime
) -> FrameMetrics | None:
    try:
        gray_image, frame_size = process_frame(frame_data)
        result_face = get_face_landmarks(face_mesh_instance, gray_image)

        if result_face is None:
            return None

        landmarks_face, landmarks = result_face

        ear = eye_detector.get_EAR(landmarks=landmarks)
        # tired, perclos_score = scorer.get_PERCLOS(t_now, fps, ear)
        gaze = eye_detector.get_Gaze_Score(
            frame=gray_image, landmarks=landmarks, frame_size=frame_size
        )
        _, roll, pitch, yaw = head_pose.get_pose(
            frame=gray_image, landmarks=landmarks, frame_size=frame_size
        )
        fatigue_score, distraction_score, attention_score = calculate_attention_scores(scorer, fps, t_now, ear, gaze, roll, pitch, yaw)

        metrics.update(fatigue_score, distraction_score, attention_score)

        if start_time is not None:
            time_on_screen = round((datetime.now() - start_time).total_seconds(), 2)
        else:
            time_on_screen = 0

        payload = FrameMetrics(
            landmarks=convert_landmarks(landmarks_face),
            attention_metrics=AttentionMetrics(
                fatigue_score=fatigue_score,
                distraction_score=distraction_score,
                attention_score=attention_score,
                time_on_screen=time_on_screen
            ),
        )

        return payload

    except Exception as e:
        print(f"Erro ao processar frame: {e}")
        traceback.print_exc()


def init_cv_dependencies():
    if not cv2.useOptimized():
        try:
            cv2.setUseOptimized(True)
        except Exception as ex:
            print("OpenCV optimization could not be set to True.", ex)

    return face_mesh(), EyeDetector(), HeadPoseEstimator(),


def calculate_attention_scores(scorer: AttentionScorer, fps: float, t_now: float, ear: float, gaze: float, roll: float, pitch: float, yaw: float):
    scorer.eval_scores(t_now, ear, gaze, roll, pitch, yaw)

    fatigue_score = min((scorer.closure_time / scorer.ear_time_thresh) * 100, 100)
    distraction_score = min((scorer.not_look_ahead_time / scorer.gaze_time_thresh) * 100, 100)
    pose_score = min((scorer.distracted_time / scorer.pose_time_thresh) * 100, 100)

    attention_score = max(100 - (fatigue_score * 0.5 + distraction_score * 0.3 + pose_score * 0.2), 0)

    return fatigue_score, distraction_score, attention_score


async def start_study_session(session: AsyncSession, user: User):
    print("Iniciando sessão de estudo...")
    print("Usuário:", user.__dict__)

    study_session_data = StudySessionCreate(
        user_id=user.id,
        start_time=datetime.now(),
    )

    return await create_study_session(session, study_session_data)


async def finalize_session(
    session: AsyncSession,
    user: User,
    study_session: StudySession,
    metrics: SessionMetrics,
    scorer: AttentionScorer,
    start_time: datetime
):
    print("Cliente desconectado.")

    end_time = datetime.now()
    duration_minutes = int((end_time - start_time).total_seconds() // 60)
    perclos = scorer.total_closed_frames / scorer.total_frames if scorer.total_frames > 0 else 0.0

    summary_data = metrics.summary()
    updated_data = StudySessionCreate(
        user_id=user.id,
        daily_summary_id=study_session.daily_summary_id,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration_minutes,
        perclos=perclos,
        **summary_data
    )

    await end_study_session(study_session.id, updated_data, session)


def convert_landmarks(landmarks_face: dict) -> FaceLandmarks:
    if landmarks_face is None:
        return None

    return FaceLandmarks(
        **{
            region: [Point2D(x=point[0], y=point[1]) for point in points]
            for region, points in landmarks_face.items()
        }
    )
