from pydantic import BaseModel

from app.services.video_normalize import NormalizedVideoResult
from app.services.video_probe import ProbedVideoMetadata

ANALYSIS_RESULT_SCHEMA_VERSION = "analysis_result.v2"
POSE_LANDMARKS_SCHEMA_VERSION = "pose_landmarks.v1"
POSE_MODEL_NAME = "mediapipe_pose_landmarker_full"
POSE_MODEL_ASSET_NAME = "pose_landmarker_full.task"
POSE_LANDMARK_FORMAT = "mediapipe_pose_33"
GAIT_ANALYSIS_SCHEMA_VERSION = "gait_analysis.v1"


class AnalysisNormalizationResult(BaseModel):
    enabled: bool
    timing_mode: str
    target_fps: float
    max_long_edge: int
    stored_object_key: str | None


class PoseLandmarksVideoMetadata(BaseModel):
    fps: float | None
    frame_count: int
    width: int
    height: int


class PoseLandmark(BaseModel):
    x: float
    y: float
    z: float
    visibility: float


class PoseLandmarkFrame(BaseModel):
    frame_index: int
    timestamp_ms: int
    pose_detected: bool
    landmarks: dict[str, PoseLandmark]


class PoseDetectionResult(BaseModel):
    model: str
    model_asset_name: str | None
    landmark_format: str
    detected_frame_count: int
    frames: list[PoseLandmarkFrame]


class PoseLandmarksResult(BaseModel):
    schema_version: str
    video: PoseLandmarksVideoMetadata
    pose: PoseDetectionResult


class GaitAnalysisResult(BaseModel):
    schema_version: str


class AnalysisResult(BaseModel):
    schema_version: str | None = None
    normalization: AnalysisNormalizationResult
    original_video: ProbedVideoMetadata
    analysis_video: ProbedVideoMetadata
    pose_landmarks: PoseLandmarksResult | None = None
    gait: GaitAnalysisResult | None = None


def build_analysis_result(
    probed_video: ProbedVideoMetadata,
    normalized_video_result: NormalizedVideoResult,
) -> AnalysisResult:
    return AnalysisResult(
        schema_version=ANALYSIS_RESULT_SCHEMA_VERSION,
        normalization=AnalysisNormalizationResult(
            enabled=True,
            timing_mode="cfr",
            target_fps=normalized_video_result.target_fps,
            max_long_edge=normalized_video_result.max_long_edge,
            stored_object_key=None,
        ),
        original_video=probed_video,
        analysis_video=normalized_video_result.metadata,
    )
