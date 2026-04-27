import json
import math
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
        "-loglevel",
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
    except FileNotFoundError as error:
        raise RuntimeError("ffprobe is not available") from error
    except subprocess.TimeoutExpired as error:
        raise ValueError("Timed out while probing uploaded video") from error

    if result.returncode != 0:
        error_message = result.stderr.strip()
        if error_message:
            print(f"ffprobe failed while probing uploaded video: {error_message}")

        raise ValueError("Uploaded object is not a valid video")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("Failed to parse video probe result") from error

    format_info = payload.get("format")
    streams = payload.get("streams")

    if not isinstance(format_info, dict) or not isinstance(streams, list):
        raise ValueError("Uploaded object has invalid video metadata")

    video_stream = None

    for stream in streams:
        if isinstance(stream, dict) and stream.get("codec_type") == "video":
            video_stream = stream
            break

    if not isinstance(video_stream, dict):
        raise ValueError("Uploaded object does not contain a video stream")

    duration_seconds = parse_duration_seconds(format_info, video_stream)

    if duration_seconds is None:
        raise ValueError("Uploaded object has invalid video duration")

    width = video_stream.get("width")

    if not isinstance(width, int) or width <= 0:
        raise ValueError("Uploaded object has invalid video width")

    height = video_stream.get("height")

    if not isinstance(height, int) or height <= 0:
        raise ValueError("Uploaded object has invalid video height")

    fps = parse_frame_rate(video_stream.get("avg_frame_rate"))
    codec_name = parse_codec_name(video_stream.get("codec_name"))
    rotation_degrees = parse_rotation_degrees(video_stream)

    return ProbedVideoMetadata(
        duration_seconds=duration_seconds,
        width=width,
        height=height,
        fps=fps,
        codec_name=codec_name,
        rotation_degrees=rotation_degrees,
    )


def parse_duration_seconds(format_info: dict, video_stream: dict) -> float | None:
    duration_seconds = parse_positive_float(format_info.get("duration"))

    if duration_seconds is not None:
        return duration_seconds

    return parse_positive_float(video_stream.get("duration"))


def parse_frame_rate(value: object) -> float | None:
    if not isinstance(value, str) or not value:
        return None

    if "/" not in value:
        try:
            frame_rate = float(value)
        except ValueError:
            return None

        if not math.isfinite(frame_rate) or frame_rate <= 0:
            return None

        return frame_rate

    numerator_text, denominator_text = value.split("/", 1)

    try:
        numerator = float(numerator_text)
        denominator = float(denominator_text)
    except ValueError:
        return None

    if (
        not math.isfinite(numerator)
        or not math.isfinite(denominator)
        or numerator <= 0
        or denominator <= 0
    ):
        return None

    return numerator / denominator


def parse_codec_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    codec_name = value.strip()

    return codec_name or None


def parse_rotation_degrees(video_stream: dict) -> int | None:
    side_data_list = video_stream.get("side_data_list")

    if isinstance(side_data_list, list):
        for side_data in side_data_list:
            if not isinstance(side_data, dict):
                continue

            rotation = side_data.get("rotation")
            parsed_rotation = parse_integer_degrees(rotation)

            if parsed_rotation is not None:
                return parsed_rotation

    tags = video_stream.get("tags")

    if isinstance(tags, dict):
        return parse_integer_degrees(tags.get("rotate"))

    return None


def parse_positive_float(value: object) -> float | None:
    try:
        parsed_value = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(parsed_value):
        return None

    return parsed_value if parsed_value > 0 else None


def parse_integer_degrees(value: object) -> int | None:
    if isinstance(value, bool):
        return None

    if not isinstance(value, (int, float, str)):
        return None

    try:
        return int(float(value))
    except (OverflowError, ValueError):
        return None
