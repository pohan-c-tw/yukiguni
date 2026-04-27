import subprocess
import tempfile

from pydantic import BaseModel

from app.services.temp_files import remove_file_if_exists
from app.services.video_probe import ProbedVideoMetadata, probe_video_file

MAX_ANALYSIS_FPS = 60.0
COMMON_FPS_VALUES = [24.0, 25.0, 30.0, 50.0, 60.0]
COMMON_FPS_TOLERANCE = 0.75
MAX_ANALYSIS_LONG_EDGE = 720
FFMPEG_TIMEOUT_SECONDS = 180


class NormalizedVideoResult(BaseModel):
    file_path: str
    metadata: ProbedVideoMetadata
    target_fps: float
    max_long_edge: int


def choose_analysis_fps(source_fps: float | None) -> float:
    if source_fps is None or source_fps <= 0:
        return 30.0

    capped_fps = min(source_fps, MAX_ANALYSIS_FPS)

    for common_fps in COMMON_FPS_VALUES:
        if abs(capped_fps - common_fps) <= COMMON_FPS_TOLERANCE:
            return common_fps

    return round(capped_fps, 3)


def build_analysis_video_filter(target_fps: float) -> str:
    scale_filter = (
        "scale="
        f"'if(gte(iw,ih),min({MAX_ANALYSIS_LONG_EDGE},iw),-2)':"
        f"'if(gte(iw,ih),-2,min({MAX_ANALYSIS_LONG_EDGE},ih))'"
    )
    return f"{scale_filter},fps={target_fps}"


def normalize_video_for_analysis(
    input_file_path: str,
    source_fps: float | None,
) -> NormalizedVideoResult:
    target_fps = choose_analysis_fps(source_fps)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        output_file_path = temp_file.name

    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        input_file_path,
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        build_analysis_video_filter(target_fps),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        output_file_path,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        remove_file_if_exists(output_file_path)
        raise RuntimeError("ffmpeg is not available") from error
    except subprocess.TimeoutExpired as error:
        remove_file_if_exists(output_file_path)
        raise ValueError("Timed out while normalizing video for analysis") from error

    if result.returncode != 0:
        remove_file_if_exists(output_file_path)
        error_message = result.stderr.strip() or "ffmpeg exited with an error"
        raise ValueError(f"Failed to normalize video for analysis: {error_message}")

    try:
        normalized_metadata = probe_video_file(output_file_path)
    except Exception:
        remove_file_if_exists(output_file_path)
        raise

    return NormalizedVideoResult(
        file_path=output_file_path,
        metadata=normalized_metadata,
        target_fps=target_fps,
        max_long_edge=MAX_ANALYSIS_LONG_EDGE,
    )
