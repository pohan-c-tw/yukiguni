import json
import subprocess

from pydantic import BaseModel

FFPROBE_TIMEOUT_SECONDS = 30


class ProbedVideoMetadata(BaseModel):
    duration_seconds: float
    width: int
    height: int


def probe_video_file(file_path: str) -> ProbedVideoMetadata:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=FFPROBE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError("Timed out while probing uploaded video") from error

    if result.returncode != 0:
        raise ValueError("Uploaded object is not a valid video")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("Failed to parse video probe result") from error

    streams = payload.get("streams")
    format_info = payload.get("format")

    if not isinstance(streams, list) or not isinstance(format_info, dict):
        raise ValueError("Uploaded object has invalid video metadata")

    video_stream = next(
        (
            stream
            for stream in streams
            if isinstance(stream, dict) and stream.get("codec_type") == "video"
        ),
        None,
    )

    if not isinstance(video_stream, dict):
        raise ValueError("Uploaded object does not contain a video stream")

    width = video_stream.get("width")
    height = video_stream.get("height")
    duration = format_info.get("duration")

    if not isinstance(width, int) or width <= 0:
        raise ValueError("Uploaded object has invalid video width")

    if not isinstance(height, int) or height <= 0:
        raise ValueError("Uploaded object has invalid video height")

    try:
        duration_seconds = float(duration)
    except (TypeError, ValueError) as error:
        raise ValueError("Uploaded object has invalid video duration") from error

    if duration_seconds <= 0:
        raise ValueError("Uploaded object has invalid video duration")

    return ProbedVideoMetadata(
        duration_seconds=duration_seconds,
        width=width,
        height=height,
    )
