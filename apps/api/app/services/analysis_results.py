from typing import Any

from app.services.video_normalize import NormalizedVideoResult
from app.services.video_probe import ProbedVideoMetadata


def build_analysis_result(
    probed_video: ProbedVideoMetadata,
    normalized_video_result: NormalizedVideoResult,
) -> dict[str, Any]:
    return {
        "normalization": {
            "enabled": True,
            "timing_mode": "cfr",
            "target_fps": normalized_video_result.target_fps,
            "max_long_edge": normalized_video_result.max_long_edge,
            "stored_object_key": None,
        },
        "original_video": probed_video.model_dump(),
        "analysis_video": normalized_video_result.metadata.model_dump(),
    }
