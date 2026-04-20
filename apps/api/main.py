import json
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

import boto3
import psycopg
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

load_dotenv()

app = FastAPI()

ALLOWED_UPLOAD_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
}
MAX_UPLOAD_FILE_SIZE_BYTES = 100 * 1024 * 1024
UPLOAD_URL_EXPIRES_IN_SECONDS = 900


def normalize_non_empty_text(value: str, field_name: str) -> str:
    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    return normalized


def validate_filename_like(value: str, field_name: str) -> str:
    normalized = normalize_non_empty_text(value, field_name)

    if "/" in normalized or "\\" in normalized:
        raise ValueError(f"{field_name} must not contain path separators")

    return normalized


def validate_upload_content_type(value: str) -> str:
    normalized = normalize_non_empty_text(value, "content_type").lower()

    if normalized not in ALLOWED_UPLOAD_CONTENT_TYPES:
        raise ValueError("unsupported content_type")

    return normalized


def validate_upload_file_size(value: int) -> int:
    if value <= 0:
        raise ValueError("file_size must be greater than 0")

    if value > MAX_UPLOAD_FILE_SIZE_BYTES:
        raise ValueError("file_size exceeds the maximum allowed size")

    return value


class R2Settings(BaseModel):
    bucket_name: str
    access_key_id: str
    secret_access_key: str
    endpoint: str


class CreateUploadUrlRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    file_size: int

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        return validate_filename_like(value, "filename")

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        return validate_upload_content_type(value)

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, value: int) -> int:
        return validate_upload_file_size(value)


class CreateUploadUrlResponse(BaseModel):
    object_key: str
    upload_url: str
    expires_in_seconds: int


class CreateJobRequest(BaseModel):
    original_filename: str = Field(min_length=1, max_length=255)
    content_type: str
    input_object_key: str

    @field_validator("original_filename")
    @classmethod
    def validate_original_filename(cls, value: str) -> str:
        return validate_filename_like(value, "original_filename")

    @field_validator("content_type")
    @classmethod
    def validate_job_content_type(cls, value: str) -> str:
        return validate_upload_content_type(value)

    @field_validator("input_object_key")
    @classmethod
    def validate_input_object_key(cls, value: str) -> str:
        return normalize_non_empty_text(value, "input_object_key")


class JobResponse(BaseModel):
    id: UUID
    status: Literal["uploaded", "validating", "processing", "done", "failed"]
    original_filename: str
    content_type: str
    input_object_key: str
    video_duration_seconds: float
    video_width: int
    video_height: int
    processing_started_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None


class UploadedObjectMetadata(BaseModel):
    content_length: int
    content_type: str


class ProbedVideoMetadata(BaseModel):
    duration_seconds: float
    width: int
    height: int


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"{name} is not set")

    return value


def get_database_url() -> str:
    return get_required_env("DATABASE_URL")


def get_r2_settings() -> R2Settings:
    return R2Settings(
        bucket_name=get_required_env("R2_BUCKET_NAME"),
        access_key_id=get_required_env("R2_ACCESS_KEY_ID"),
        secret_access_key=get_required_env("R2_SECRET_ACCESS_KEY"),
        endpoint=get_required_env("R2_ENDPOINT"),
    )


def create_r2_client():
    settings = get_r2_settings()

    return boto3.client(
        "s3",
        endpoint_url=settings.endpoint,
        aws_access_key_id=settings.access_key_id,
        aws_secret_access_key=settings.secret_access_key,
        region_name="auto",
    )


def build_upload_object_key(filename: str) -> str:
    return f"uploads/{uuid4()}-{filename}"


def generate_presigned_upload_url(object_key: str, content_type: str) -> str:
    settings = get_r2_settings()
    r2_client = create_r2_client()

    return r2_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.bucket_name,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=UPLOAD_URL_EXPIRES_IN_SECONDS,
    )


def get_uploaded_object_metadata(object_key: str) -> UploadedObjectMetadata:
    settings = get_r2_settings()
    r2_client = create_r2_client()

    try:
        response = r2_client.head_object(
            Bucket=settings.bucket_name,
            Key=object_key,
        )
    except ClientError as error:
        status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        error_code = error.response.get("Error", {}).get("Code")

        if status_code == 404 or error_code in {"404", "NoSuchKey"}:
            raise HTTPException(
                status_code=400, detail="Uploaded object not found"
            ) from error

        raise HTTPException(
            status_code=502,
            detail="Failed to read uploaded object metadata",
        ) from error

    content_length = response.get("ContentLength")
    content_type = response.get("ContentType")

    if not isinstance(content_length, int) or content_length <= 0:
        raise HTTPException(status_code=400, detail="Uploaded object has invalid size")

    if content_length > MAX_UPLOAD_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400, detail="Uploaded object exceeds the maximum allowed size"
        )

    if not isinstance(content_type, str):
        raise HTTPException(
            status_code=400, detail="Uploaded object is missing content type"
        )

    normalized_content_type = validate_upload_content_type(content_type)

    return UploadedObjectMetadata(
        content_length=content_length,
        content_type=normalized_content_type,
    )


def download_uploaded_object_to_tempfile(object_key: str) -> str:
    r2_client = create_r2_client()
    _, suffix = os.path.splitext(object_key)

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file_path = temp_file.name

    try:
        with open(temp_file_path, "wb") as file_handle:
            r2_client.download_fileobj(
                Bucket=get_r2_settings().bucket_name,
                Key=object_key,
                Fileobj=file_handle,
            )
    except ClientError as error:
        os.unlink(temp_file_path)
        raise HTTPException(
            status_code=502,
            detail="Failed to download uploaded object",
        ) from error

    return temp_file_path


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
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=400, detail="Uploaded object is not a valid video"
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=502,
            detail="Failed to parse video probe result",
        ) from error

    streams = payload.get("streams")
    format_info = payload.get("format")

    if not isinstance(streams, list) or not isinstance(format_info, dict):
        raise HTTPException(
            status_code=400, detail="Uploaded object has invalid video metadata"
        )

    video_stream = next(
        (
            stream
            for stream in streams
            if isinstance(stream, dict) and stream.get("codec_type") == "video"
        ),
        None,
    )

    if not isinstance(video_stream, dict):
        raise HTTPException(
            status_code=400, detail="Uploaded object does not contain a video stream"
        )

    width = video_stream.get("width")
    height = video_stream.get("height")
    duration = format_info.get("duration")

    if not isinstance(width, int) or width <= 0:
        raise HTTPException(
            status_code=400, detail="Uploaded object has invalid video width"
        )

    if not isinstance(height, int) or height <= 0:
        raise HTTPException(
            status_code=400, detail="Uploaded object has invalid video height"
        )

    try:
        duration_seconds = float(duration)
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=400, detail="Uploaded object has invalid video duration"
        ) from error

    if duration_seconds <= 0:
        raise HTTPException(
            status_code=400, detail="Uploaded object has invalid video duration"
        )

    return ProbedVideoMetadata(
        duration_seconds=duration_seconds,
        width=width,
        height=height,
    )


def validate_uploaded_video_file(object_key: str) -> ProbedVideoMetadata:
    temp_file_path = download_uploaded_object_to_tempfile(object_key)

    try:
        return probe_video_file(temp_file_path)
    finally:
        os.unlink(temp_file_path)


def validate_uploaded_object_for_job(payload: CreateJobRequest) -> ProbedVideoMetadata:
    metadata = get_uploaded_object_metadata(payload.input_object_key)

    if metadata.content_type != payload.content_type:
        raise HTTPException(
            status_code=400,
            detail="Uploaded object content type does not match the job request",
        )

    return validate_uploaded_video_file(payload.input_object_key)


def build_job_response(
    row: tuple[
        UUID,
        str,
        str,
        str,
        str,
        float,
        int,
        int,
        datetime | None,
        datetime | None,
        datetime | None,
    ],
) -> JobResponse:
    return JobResponse(
        id=row[0],
        status=row[1],
        original_filename=row[2],
        content_type=row[3],
        input_object_key=row[4],
        video_duration_seconds=row[5],
        video_width=row[6],
        video_height=row[7],
        processing_started_at=row[8],
        completed_at=row[9],
        failed_at=row[10],
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/uploads/presign", response_model=CreateUploadUrlResponse)
def create_upload_url(payload: CreateUploadUrlRequest) -> CreateUploadUrlResponse:
    object_key = build_upload_object_key(payload.filename)
    upload_url = generate_presigned_upload_url(object_key, payload.content_type)

    return CreateUploadUrlResponse(
        object_key=object_key,
        upload_url=upload_url,
        expires_in_seconds=UPLOAD_URL_EXPIRES_IN_SECONDS,
    )


@app.post("/jobs", response_model=JobResponse)
def create_job(payload: CreateJobRequest) -> JobResponse:
    probed_video = validate_uploaded_object_for_job(payload)
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            job_id = uuid4()
            cur.execute(
                """
                INSERT INTO analysis_jobs (
                    id,
                    status,
                    original_filename,
                    content_type,
                    input_object_key,
                    video_duration_seconds,
                    video_width,
                    video_height
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    status,
                    original_filename,
                    content_type,
                    input_object_key,
                    video_duration_seconds,
                    video_width,
                    video_height,
                    processing_started_at,
                    completed_at,
                    failed_at
                """,
                (
                    job_id,
                    "uploaded",
                    payload.original_filename,
                    payload.content_type,
                    payload.input_object_key,
                    probed_video.duration_seconds,
                    probed_video.width,
                    probed_video.height,
                ),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="Failed to create job")

    return build_job_response(row)


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID) -> JobResponse:
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    status,
                    original_filename,
                    content_type,
                    input_object_key,
                    video_duration_seconds,
                    video_width,
                    video_height,
                    processing_started_at,
                    completed_at,
                    failed_at
                FROM analysis_jobs
                WHERE id = %s
                """,
                (job_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return build_job_response(row)
