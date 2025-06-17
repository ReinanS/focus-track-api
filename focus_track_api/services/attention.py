import base64

import cv2
from focus_track_api.services.attention_scorer import AttentionScorer
from focus_track_api.services.eye_detector import EyeDetector
from focus_track_api.services.pose_estimation import HeadPoseEstimator
import numpy as np
import mediapipe as mp

from focus_track_api.utils.constants import EYES_LMS_NUMS, FACE_BOUNDARY, INNER_LIP, LEFT_EYE, LEFT_EYEBROW, LEFT_IRIS, LEFT_IRIS_NUM, NOSE, OUTER_LIP, RIGHT_EYE, RIGHT_EYEBROW, RIGHT_IRIS, RIGHT_IRIS_NUM
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
  # get the frame size
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
                for landmark in (results.multi_face_landmarks[0].landmark[i] for i in indices)
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
            'outer_lips': OUTER_LIP
        }

        # Construir o dicionário de landmarks usando a função auxiliar
        landmarks_dict = {region: process_landmarks(indices) for region, indices in regions.items()}

        return landmarks_dict, landmarks

    return None
 
  
def attention_monitor(data: bytes, face_mesh,  t_now: float, fps: int, eye_detector: EyeDetector, head_pose: HeadPoseEstimator, scorer: AttentionScorer):  
  gray_image, frame_size = process_frame(data)
  landmarks_face, landmarks = get_face_landmarks(face_mesh, gray_image)
  # compute the EAR score of the eyes
  ear = eye_detector.get_EAR(landmarks=landmarks)
   # compute the PERCLOS score and state of tiredness
  tired, perclos_score = scorer.get_PERCLOS(t_now, fps, ear) 
  # compute the Gaze Score
  gaze = eye_detector.get_Gaze_Score(
      frame=gray_image, landmarks=landmarks, frame_size=frame_size
  )
  
  # compute the head pose
  _, roll, pitch, yaw = head_pose.get_pose(
      frame=gray_image, landmarks=landmarks, frame_size=frame_size
  )
  
  # evaluate the scores for EAR, GAZE and HEAD POSE
  asleep, looking_away, distracted = scorer.eval_scores(
      t_now=t_now,
      ear_score=ear,
      gaze_score=gaze,
      head_roll=roll,
      head_pitch=pitch,
      head_yaw=yaw,
  )
  
  # print(gaze)
  
  if(looking_away):
    print("Looking away")
  if(distracted):
    print("Distracted")
  if(asleep):
    print("Asleep")
  if(tired):
    print("Tired")
  
  return {
          "landmarks": landmarks_face,
          "direction": "Looking Forward",
          "drowsy": False,
          "blink_detected": False,
          "yawn_detected": False,
          "iris_visibility": 0.8
        }

# def attention_monitor(img: str):
#   image = process_image(img)
#   landmarks = biggest_face_landmarks(image)

#   try:
#     frame_size = image.shape[1], image.shape[0]
#     print('get_eyes_landmarks')
#     eyes_landmarks = get_eyes_landmarks(landmarks, frame_size)
    
#     return {
#     "scores": {
#         "EAR": 0.85,
#         "PERCLOS": 0.75,
#         "Gaze": 0.90
#     },
#     "orientation": {
#         "Roll": 10,
#         "Pitch": 5,
#         "Yaw": 0
#     },
#     "alert": "No alert",
#     "facialLandmarks": {
#         "eyes": eyes_landmarks,
#         "mouth": [
#             {"x": 350, "y": 300},
#             {"x": 360, "y": 310},
#             {"x": 370, "y": 300}
#         ]
#     }
# }

#   except Exception as e:
#     print(e)
    



#   # if image is not None:
#   #     cv2.imshow("Image", image)  # "Image" é o nome da janela
#   #     cv2.waitKey(0)  # Aguarda uma tecla para fechar a janela
#   #     cv2.destroyAllWindows()  # Fecha a janela após a tecla ser pressionada
#   # else:
#   #     print("Erro: A imagem não foi processada corretamente.")


# def process_image(img: str):
#   base64_data = img.split(",")[1]
#   gray_image = from_base64_to_numpy(base64_data)
#   gray_image = cv2.flip(gray_image, 2)

#   gray_image = np.expand_dims(gray_image, axis=2)
#   gray_image = np.concatenate([gray_image, gray_image, gray_image], axis=2)

#   return gray_image

# def from_base64_to_numpy(img: str): 
#   # Step 1: Decode the base64 string to binary data
#   image_data = base64.b64decode(img)

#   # Step 2: Convert binary data to a numpy array
#   # We assume the input image is in a common format like PNG or JPEG
#   image_array = np.frombuffer(image_data, dtype=np.uint8)

#   # Step 3: Decode the numpy array to get the image in BGR format
#   image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

#   # Step 4: Convert the image to grayscale
#   gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  
#   return gray_image

# def biggest_face_landmarks(image):
#   face_mesh = mp.solutions.face_mesh.FaceMesh(
#     static_image_mode=False,
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5,
#     refine_landmarks=True,
#   )

#   lms = face_mesh.process(image).multi_face_landmarks

#   if lms is not None:
#       biggest_face = get_landmarks(lms)
#       if biggest_face is None:
#          raise Exception("No face detected")
      
#       return biggest_face
          


# def get_landmarks(lms):
#     if not lms:
#         raise Exception("Nenhum landmark detectado")
    
#     surface = 0
#     biggest_face = None
#     for lms0 in lms:
#         landmarks = [np.array([point.x, point.y, point.z]) for point in lms0.landmark]
#         landmarks = np.array(landmarks)
#         # Limitar valores
#         landmarks[landmarks[:, 0] < 0.0, 0] = 0.0
#         landmarks[landmarks[:, 0] > 1.0, 0] = 1.0
#         landmarks[landmarks[:, 1] < 0.0, 1] = 0.0
#         landmarks[landmarks[:, 1] > 1.0, 1] = 1.0

#         dx = landmarks[:, 0].max() - landmarks[:, 0].min()
#         dy = landmarks[:, 1].max() - landmarks[:, 1].min()
#         new_surface = dx * dy
#         if new_surface > surface:
#             surface = new_surface
#             biggest_face = landmarks

#     return biggest_face


# def get_eyes_landmarks(lms, frame_size):
#     # Multiplica as coordenadas pelo tamanho do frame e converte para int
#     left_iris_center = (lms[LEFT_IRIS_NUM, :2] * frame_size).astype(int).tolist()
#     right_iris_center = (lms[RIGHT_IRIS_NUM, :2] * frame_size).astype(int).tolist()
    
#     # Calcula as coordenadas do contorno dos olhos
#     eyes_outline = [
#         (lms[idx, :2] * frame_size).astype(int).tolist() for idx in EYES_LMS_NUMS
#     ]

#     return left_iris_center, right_iris_center, eyes_outline
