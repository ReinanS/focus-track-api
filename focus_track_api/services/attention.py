import json
import traceback
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

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

# Constantes para thresholds de eventos críticos
DISTRACTION_THRESHOLD = 70
FATIGUE_THRESHOLD = 60
ATTENTION_THRESHOLD = 30
DEBUG_LOG_THRESHOLD = 50
PERCLOS_DEBUG_START = 50
PERCLOS_DEBUG_END = 70
EVENT_DUPLICATE_WINDOW = 30
MAX_EVENTS_PER_SESSION = 50
MIN_SESSION_DURATION = 60


def ensure_timezone_aware(dt: datetime) -> datetime:
    """Garante que um datetime tenha timezone UTC"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def safe_float(value) -> float:
    """Converte um valor para float de forma segura, lidando com arrays NumPy"""
    if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
        # É um array ou iterável, pegar o primeiro elemento
        return float(value[0] if len(value) > 0 else 0)
    return float(value)


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


def get_face_landmarks(
    face_mesh, frame: np.ndarray
) -> tuple[dict, list] | None:
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

        return (landmarks_dict, landmarks)

    return None


async def handle_session_status(
    study_session: Optional[StudySession],
    session: Optional[AsyncSession],
    face_detected: bool,
) -> dict | None:
    """Gerencia o status da sessão baseado na detecção facial"""
    if not study_session or not session:
        return None

    current_time = datetime.now(timezone.utc)

    if not face_detected:
        # Rosto não detectado - pausar sessão se estiver ativa
        if study_session.status == 'active':
            study_session.status = 'paused'
            study_session.paused_at = current_time
            await session.commit()
            print('Sessão pausada - rosto não detectado')

        return {
            'error': 'FACE_NOT_FOUND',
            'message': 'Rosto não detectado. Posicione-se melhor na frente da câmera.',
            'type': 'FACE_DETECTION',
            'session_status': study_session.status,
        }
    # Rosto detectado - gerenciar status da sessão
    elif study_session.status == 'waiting':
        # Primeira detecção - ativar sessão
        study_session.status = 'active'
        await session.commit()
        print('Sessão ativada - rosto detectado pela primeira vez')
    elif study_session.status == 'paused':
        # Retomar sessão pausada
        if study_session.paused_at:
            paused_duration = (
                current_time - study_session.paused_at
            ).total_seconds()
            study_session.total_paused_time += paused_duration
            study_session.paused_at = None

        study_session.status = 'active'
        await session.commit()
        print('Sessão retomada - rosto detectado novamente')

    return None


async def process_attention_metrics(
    landmarks: list,
    gray_image: np.ndarray,
    frame_size: tuple,
    eye_detector: EyeDetector,
    head_pose: HeadPoseEstimator,
    scorer: AttentionScorer,
    fps: float,
    t_now: float,
) -> tuple[float, float, float]:
    """Processa métricas de atenção (EAR, gaze, pose)"""
    ear = eye_detector.get_EAR(landmarks=landmarks)
    gaze = eye_detector.get_Gaze_Score(
        frame=gray_image, landmarks=landmarks, frame_size=frame_size
    )
    _, roll, pitch, yaw = head_pose.get_pose(
        frame=gray_image, landmarks=landmarks, frame_size=frame_size
    )

    fatigue_score, distraction_score, attention_score = (
        calculate_attention_scores(
            scorer, fps, t_now, ear, gaze, roll, pitch, yaw
        )
    )

    return fatigue_score, distraction_score, attention_score


async def check_critical_events(
    study_session: Optional[StudySession],
    session: Optional[AsyncSession],
    fatigue_score: float,
    distraction_score: float,
    attention_score: float,
):
    """Verifica e adiciona eventos críticos baseados nos scores"""
    if not study_session or not session:
        return

    current_time = datetime.now(timezone.utc)
    time_str = current_time.strftime('%H:%M:%S')

    # Evento de alta distração (baseado no tempo acumulado)
    if distraction_score > DISTRACTION_THRESHOLD:
        event = {
            'time': time_str,
            'type': 'distraction',
            'level': 'high',
            'score': round(distraction_score, 1),
            'message': 'Alta distração detectada',
        }
        await add_critical_event(study_session, event, session)

    # Evento de fadiga crítica
    if fatigue_score > FATIGUE_THRESHOLD:
        event = {
            'time': time_str,
            'type': 'fatigue',
            'level': 'medium',
            'score': round(fatigue_score, 1),
            'message': 'Fadiga detectada',
        }
        await add_critical_event(study_session, event, session)

    # Evento de atenção muito baixa
    if attention_score < ATTENTION_THRESHOLD:
        print(
            f'DEBUG - Atenção abaixo do threshold ({ATTENTION_THRESHOLD}%): {attention_score:.1f}%'
        )
        event = {
            'time': time_str,
            'type': 'attention',
            'level': 'critical',
            'score': round(attention_score, 1),
            'message': 'Atenção muito baixa',
        }
        await add_critical_event(study_session, event, session)


def create_frame_payload(
    landmarks_face: dict,
    fatigue_score: float,
    distraction_score: float,
    attention_score: float,
    start_time: Optional[datetime],
    study_session: Optional[StudySession],
) -> dict:
    """Cria o payload de resposta do frame"""
    if start_time is not None:
        current_time = datetime.now(timezone.utc)
        start_time_aware = ensure_timezone_aware(start_time)
        time_on_screen = round(
            (current_time - start_time_aware).total_seconds(), 2
        )
    else:
        time_on_screen = 0

    # Criar payload base
    payload = FrameMetrics(
        landmarks=convert_landmarks(landmarks_face),
        attention_metrics=AttentionMetrics(
            fatigue_score=fatigue_score,
            distraction_score=distraction_score,
            attention_score=attention_score,
            time_on_screen=time_on_screen,
        ),
    )

    # Adicionar informações de status da sessão se disponível
    if study_session:
        payload_dict = payload.model_dump()
        payload_dict['session_status'] = study_session.status
        payload_dict['total_paused_time'] = study_session.total_paused_time
        if study_session.paused_at:
            payload_dict['paused_at'] = study_session.paused_at.isoformat()
        else:
            payload_dict['paused_at'] = None
        return payload_dict

    return payload


async def handle_frame(
    frame_data: bytes,
    face_mesh_instance,
    eye_detector: EyeDetector,
    t_now: float,
    fps: float,
    head_pose: HeadPoseEstimator,
    scorer: AttentionScorer,
    metrics: SessionMetrics,
    start_time: datetime,
    study_session: Optional[StudySession] = None,
    session: Optional[AsyncSession] = None,
) -> FrameMetrics | dict:
    """Processa um frame e retorna métricas de atenção"""
    try:
        # 1. Processar frame e extrair landmarks
        gray_image, frame_size = process_frame(frame_data)
        result_face = get_face_landmarks(face_mesh_instance, gray_image)

        # 2. Gerenciar status da sessão baseado na detecção facial
        face_detected = result_face is not None
        status_error = await handle_session_status(
            study_session, session, face_detected
        )
        if status_error:
            return status_error

        if result_face is None:
            return {
                'error': 'FACE_NOT_FOUND',
                'message': 'Rosto não detectado. Posicione-se melhor na frente da câmera.',
                'type': 'FACE_DETECTION',
                'session_status': study_session.status
                if study_session
                else 'none',
            }

        # 3. Extrair landmarks
        landmarks_face, landmarks = result_face

        # 4. Processar métricas de atenção
        (
            fatigue_score,
            distraction_score,
            attention_score,
        ) = await process_attention_metrics(
            landmarks,
            gray_image,
            frame_size,
            eye_detector,
            head_pose,
            scorer,
            fps,
            t_now,
        )

        # 5. Atualizar métricas da sessão
        metrics.update(fatigue_score, distraction_score, attention_score)

        # 6. Verificar eventos críticos
        await check_critical_events(
            study_session,
            session,
            fatigue_score,
            distraction_score,
            attention_score,
        )

        # 7. Criar payload de resposta
        return create_frame_payload(
            landmarks_face,
            fatigue_score,
            distraction_score,
            attention_score,
            start_time,
            study_session,
        )

    except Exception as e:
        print(f'Erro ao processar frame: {e}')
        traceback.print_exc()
        return {
            'error': 'PROCESSING_ERROR',
            'message': f'Erro ao processar frame: {str(e)}',
            'type': 'PROCESSING',
        }


def init_cv_dependencies():
    if not cv2.useOptimized():
        try:
            cv2.setUseOptimized(True)
        except Exception as ex:
            print('OpenCV optimization could not be set to True.', ex)

    return (
        face_mesh(),
        EyeDetector(),
        HeadPoseEstimator(),
    )


def calculate_attention_scores(
    scorer: AttentionScorer,
    fps: float,
    t_now: float,
    ear: float,
    gaze: float,
    roll: float,
    pitch: float,
    yaw: float,
):
    # Avalia os scores básicos
    scorer.eval_scores(t_now, ear, gaze, roll, pitch, yaw)

    # Calcula PERCLOS para uma métrica mais precisa de fadiga
    _, perclos_score = scorer.get_PERCLOS(t_now, fps, ear)

    # Calcula fatigue_score baseado no PERCLOS (mais preciso)
    fatigue_score = min(
        perclos_score * 100, 100
    )  # PERCLOS já é uma porcentagem

    # Calcula distraction_score baseado no tempo de não olhar para frente
    distraction_score = min(
        (scorer.not_look_ahead_time / scorer.gaze_time_thresh) * 100, 100
    )

    # Calcula pose_score baseado no tempo de pose distraída
    pose_score = min(
        (scorer.distracted_time / scorer.pose_time_thresh) * 100, 100
    )

    # Calcula attention_score com pesos melhorados
    # Fadiga tem peso maior (0.4) pois é mais crítica para estudos
    # Distração visual tem peso médio (0.35)
    # Pose tem peso menor (0.25) pois é menos crítica
    attention_score = max(
        100
        - (fatigue_score * 0.4 + distraction_score * 0.35 + pose_score * 0.25),
        0,
    )

    return fatigue_score, distraction_score, attention_score


async def start_study_session(session: AsyncSession, user: User):
    current_time = datetime.now(tz=ZoneInfo('UTC'))
    study_session_data = StudySessionCreate(
        user_id=user.id,
        start_time=current_time,
    )

    return await create_study_session(session, study_session_data)


async def finalize_session(
    session: AsyncSession,
    user: User,
    study_session: StudySession,
    metrics: SessionMetrics,
    scorer: AttentionScorer,
):
    print('Cliente desconectado.')

    end_time = datetime.now(tz=ZoneInfo('UTC'))
    session_start_time = ensure_timezone_aware(study_session.start_time)
    effective_end_time = end_time - timedelta(
        seconds=study_session.total_paused_time
    )

    # Se a sessão efetiva durou menos de 1 minuto, remove ela
    effective_duration = (
        effective_end_time - session_start_time
    ).total_seconds()
    if effective_duration < MIN_SESSION_DURATION:
        await session.delete(study_session)
        await session.commit()
        return

    # Calcula PERCLOS final baseado nos frames acumulados durante a sessão
    perclos = (
        scorer.total_closed_frames / scorer.total_frames
        if scorer.total_frames > 0
        else 0.0
    )
    perclos_percentage = perclos * 100

    summary_data = metrics.summary()
    updated_data = StudySessionCreate(
        user_id=user.id,
        daily_summary_id=study_session.daily_summary_id,
        start_time=study_session.start_time,
        end_time=effective_end_time,
        perclos=perclos_percentage,
        critical_events=study_session.critical_events,
        **summary_data,
    )

    print(f'Debug - Finalizando sessão com dados: {summary_data}')

    # Atualizar status para finished
    study_session.status = 'finished'
    await session.commit()

    await end_study_session(study_session.id, updated_data, session)


def convert_landmarks(landmarks_face: dict | None) -> FaceLandmarks | None:
    if landmarks_face is None:
        return None

    return FaceLandmarks(**{
        region: [Point2D(x=point[0], y=point[1]) for point in points]
        for region, points in landmarks_face.items()
    })


def _parse_event_time(
    event_time_str: str, current_time: datetime
) -> Optional[datetime]:
    """Converte string de tempo para datetime com timezone"""
    try:
        print(f'DEBUG - Convertendo tempo: {event_time_str}')
        event_time = datetime.strptime(event_time_str, '%H:%M:%S')
        result = current_time.replace(
            hour=event_time.hour,
            minute=event_time.minute,
            second=event_time.second,
            microsecond=0,
        )
        print(f'DEBUG - Tempo convertido: {result}')
        return result
    except Exception as e:
        print(f'Erro ao converter tempo do evento: {e}')
        return None


def _is_duplicate_event(
    existing_event: dict,
    new_event: dict,
    event_datetime: datetime,
    current_time: datetime,
) -> bool:
    """Verifica se um evento é duplicata de um existente"""
    print(
        f'DEBUG - Verificando duplicata: {new_event["type"]} vs {existing_event.get("type")}'
    )

    if (
        existing_event.get('type') != new_event['type']
        or existing_event.get('level') != new_event['level']
    ):
        print('DEBUG - Tipos diferentes, não é duplicata')
        return False

    try:
        existing_time = datetime.strptime(existing_event['time'], '%H:%M:%S')
        existing_datetime = current_time.replace(
            hour=existing_time.hour,
            minute=existing_time.minute,
            second=existing_time.second,
            microsecond=0,
        )

        time_diff = abs((event_datetime - existing_datetime).total_seconds())
        is_duplicate = time_diff < EVENT_DUPLICATE_WINDOW
        print(
            f'DEBUG - Diferença de tempo: {time_diff:.1f}s, é duplicata: {is_duplicate}'
        )
        return is_duplicate
    except Exception as e:
        print(f'Erro ao comparar tempos: {e}')
        return False


async def add_critical_event(
    study_session: StudySession, event: dict, session: AsyncSession
):
    """Adiciona um evento crítico à sessão de estudo"""
    try:
        print(f'Tentando adicionar evento crítico: {event}')
        print(f'StudySession ID: {study_session.id}')
        print(f'StudySession status: {study_session.status}')

        # Carregar eventos existentes ou criar lista vazia
        current_events = []
        if study_session.critical_events:
            try:
                current_events = json.loads(study_session.critical_events)
                print(f'Eventos existentes carregados: {len(current_events)}')
            except json.JSONDecodeError:
                print(
                    'Erro ao decodificar eventos existentes, criando lista vazia'
                )
                current_events = []

        # Verificar se já existe um evento similar nos últimos 30 segundos
        current_time = datetime.now(timezone.utc)
        event_datetime = _parse_event_time(event['time'], current_time)

        if event_datetime:
            for existing_event in current_events:
                if _is_duplicate_event(
                    existing_event, event, event_datetime, current_time
                ):
                    print(
                        f'Evento similar já existe nos últimos {EVENT_DUPLICATE_WINDOW}s, ignorando: {event}'
                    )
                    return

        # Adicionar novo evento
        current_events.append(event)
        print(
            f'Novo evento adicionado. Total de eventos: {len(current_events)}'
        )

        # Limitar a 50 eventos por sessão para evitar sobrecarga
        if len(current_events) > MAX_EVENTS_PER_SESSION:
            current_events = current_events[-MAX_EVENTS_PER_SESSION:]
            print(f'Lista de eventos limitada a {MAX_EVENTS_PER_SESSION}')

        # Salvar eventos na sessão
        study_session.critical_events = json.dumps(current_events)
        print(f'JSON a ser salvo: {study_session.critical_events}')

        await session.commit()
        print('Commit realizado com sucesso')

    except Exception as e:
        print(f'Erro ao adicionar evento crítico: {e}')
        traceback.print_exc()
