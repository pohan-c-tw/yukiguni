import json
import subprocess

from pydantic import BaseModel

FFPROBE_TIMEOUT_SECONDS = 30


class ProbedVideoMetadata(BaseModel):
    duration_seconds: float
    width: int
    height: int
    fps: float | None = None
    codec_name: str | None = None
    rotation_degrees: int | None = None


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
    fps = parse_frame_rate(video_stream.get("avg_frame_rate"))
    codec_name = video_stream.get("codec_name")
    rotation_degrees = parse_rotation_degrees(video_stream)

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
        fps=fps,
        codec_name=codec_name if isinstance(codec_name, str) else None,
        rotation_degrees=rotation_degrees,
    )


def parse_frame_rate(value: object) -> float | None:
    if not isinstance(value, str) or not value:
        return None

    if "/" not in value:
        try:
            frame_rate = float(value)
        except ValueError:
            return None
        return frame_rate if frame_rate > 0 else None

    numerator_text, denominator_text = value.split("/", 1)

    try:
        numerator = float(numerator_text)
        denominator = float(denominator_text)
    except ValueError:
        return None

    if numerator <= 0 or denominator <= 0:
        return None

    return numerator / denominator


def parse_rotation_degrees(video_stream: dict) -> int | None:
    tags = video_stream.get("tags")

    if not isinstance(tags, dict):
        return None

    rotation = tags.get("rotate")

    if not isinstance(rotation, str):
        return None

    try:
        return int(float(rotation))
    except ValueError:
        return None
