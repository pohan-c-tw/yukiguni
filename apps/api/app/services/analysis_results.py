from pydantic import BaseModel

from app.services.video_normalize import NormalizedVideoResult
from app.services.video_probe import ProbedVideoMetadata


class AnalysisNormalizationResult(BaseModel):
    enabled: bool
    timing_mode: str
    target_fps: float
    max_long_edge: int
    stored_object_key: str | None


class AnalysisResult(BaseModel):
    normalization: AnalysisNormalizationResult
    original_video: ProbedVideoMetadata
    analysis_video: ProbedVideoMetadata


def build_analysis_result(
    probed_video: ProbedVideoMetadata,
    normalized_video_result: NormalizedVideoResult,
) -> AnalysisResult:
    return AnalysisResult(
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
