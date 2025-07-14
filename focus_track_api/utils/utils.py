import json

import cv2
import numpy as np


def load_camera_parameters(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            if file_path.endswith('.json'):
                data = json.load(file)
            else:
                raise ValueError('Unsupported file format. Use JSON or YAML.')
            return (
                np.array(data['camera_matrix'], dtype='double'),
                np.array(data['dist_coeffs'], dtype='double'),
            )
    except Exception as e:
        print(f'Failed to load camera parameters: {e}')
        return None, None


def resize(frame, scale_percent):
    """
    Resize the image maintaining the aspect ratio
    :param frame: opencv image/frame
    :param scale_percent: int
        scale factor for resizing the image
    :return:
    resized: rescaled opencv image/frame
    """
    width = int(frame.shape[1] * scale_percent / 100)
    height = int(frame.shape[0] * scale_percent / 100)
    dim = (width, height)

    resized = cv2.resize(frame, dim, interpolation=cv2.INTER_LINEAR)
    return resized


def get_landmarks(lms):
    surface = 0
    for lms0 in lms:
        landmarks = [
            np.array([point.x, point.y, point.z]) for point in lms0.landmark
        ]

        landmarks = np.array(landmarks)

        landmarks[landmarks[:, 0] < 0.0, 0] = 0.0
        landmarks[landmarks[:, 0] > 1.0, 0] = 1.0
        landmarks[landmarks[:, 1] < 0.0, 1] = 0.0
        landmarks[landmarks[:, 1] > 1.0, 1] = 1.0

        dx = landmarks[:, 0].max() - landmarks[:, 0].min()
        dy = landmarks[:, 1].max() - landmarks[:, 1].min()
        new_surface = dx * dy
        if new_surface > surface:
            biggest_face = landmarks

    return biggest_face


def get_face_area(face):
    """
    Computes the area of the bounding box ROI of the face detected by the dlib face detector
    It's used to sort the detected faces by the box area

    :param face: dlib bounding box of a detected face in faces
    :return: area of the face bounding box
    """
    return abs((face.left() - face.right()) * (face.bottom() - face.top()))


def show_keypoints(keypoints, frame):
    """
    Draw circles on the opencv frame over the face keypoints predicted by the dlib predictor

    :param keypoints: dlib iterable 68 keypoints object
    :param frame: opencv frame
    :return: frame
        Returns the frame with all the 68 dlib face keypoints drawn
    """
    for n in range(0, 68):
        x = keypoints.part(n).x
        y = keypoints.part(n).y
        cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)
        return frame


def midpoint(p1, p2):
    """
    Compute the midpoint between two dlib keypoints

    :param p1: dlib single keypoint
    :param p2: dlib single keypoint
    :return: array of x,y coordinated of the midpoint between p1 and p2
    """
    return np.array([int((p1.x + p2.x) / 2), int((p1.y + p2.y) / 2)])


def get_array_keypoints(landmarks, dtype='int', verbose: bool = False):
    """
    Converts all the iterable dlib 68 face keypoint in a numpy array of shape 68,2

    :param landmarks: dlib iterable 68 keypoints object
    :param dtype: dtype desired in output
    :param verbose: if set to True, prints array of keypoints (default is False)
    :return: points_array
        Numpy array containing all the 68 keypoints (x,y) coordinates
        The shape is 68,2
    """
    points_array = np.zeros((68, 2), dtype=dtype)
    for i in range(0, 68):
        points_array[i] = (landmarks.part(i).x, landmarks.part(i).y)

    if verbose:
        print(points_array)

    return points_array


def rot_mat_to_euler(rmat):
    """
    Converts a rotation matrix to Euler angles in degrees.

    Parameters
    ----------
    rmat: np.ndarray
        A 3x3 rotation matrix.

    Returns
    -------
    np.ndarray
        Euler angles [roll (x), pitch (y), yaw (z)] in degrees, rounded to two decimal places.
    """
    TOLERANCE = 1e-6
    DEG_PER_RAD = 180.0 / np.pi
    DIMENSION = 3
    ZERO_ANGLE = 0

    rtr = np.transpose(rmat)
    r_identity = np.matmul(rtr, rmat)
    identity_matrix = np.identity(DIMENSION, dtype=rmat.dtype)

    if np.linalg.norm(r_identity - identity_matrix) < TOLERANCE:
        sy = np.sqrt((rmat[0, 0] ** 2) + (rmat[1, 0] ** 2))
        is_singular = sy < TOLERANCE

        if not is_singular:
            x = np.arctan2(rmat[2, 1], rmat[2, 2])  # roll
            y = np.arctan2(-rmat[2, 0], sy)  # pitch
            z = np.arctan2(rmat[1, 0], rmat[0, 0])  # yaw
        else:
            x = np.arctan2(-rmat[1, 2], rmat[1, 1])
            y = np.arctan2(-rmat[2, 0], sy)
            z = ZERO_ANGLE

        # Correção dos ângulos para manter consistência
        x = np.pi - abs(x) if x > 0 else -(np.pi + x)
        z = np.pi - abs(z) if z > 0 else -(np.pi + z)

        return (np.array([x, y, z]) * DEG_PER_RAD).round(2)
    else:
        print("Isn't a rotation matrix")
