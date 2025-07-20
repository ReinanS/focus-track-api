from typing import List

from pydantic import BaseModel


class Point2D(BaseModel):
    x: float
    y: float


class RegionLandmarks(BaseModel):
    RootModel: List[Point2D]


class FaceLandmarks(BaseModel):
    face_boundary: List[Point2D]
    left_eyebrow: List[Point2D]
    right_eyebrow: List[Point2D]
    left_eye: List[Point2D]
    right_eye: List[Point2D]
    left_iris: List[Point2D]
    right_iris: List[Point2D]
    nose: List[Point2D]
    inner_lips: List[Point2D]
    outer_lips: List[Point2D]


class AttentionMetrics(BaseModel):
    fatigue_score: float
    distraction_score: float
    attention_score: float
    time_on_screen: float


class FrameMetrics(BaseModel):
    landmarks: FaceLandmarks
    attention_metrics: AttentionMetrics
