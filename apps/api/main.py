from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

import psycopg
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from job_queue import get_job_queue
from r2_storage import (
    UploadedObjectMetadata,
    build_upload_object_key,
    generate_presigned_upload_url,
    get_uploaded_object_metadata,
)
from settings import get_database_url
from tasks import process_analysis_job

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
    video_duration_seconds: float | None
    video_width: int | None
    video_height: int | None
    processing_started_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None


def validate_uploaded_object_for_job(
    payload: CreateJobRequest,
) -> UploadedObjectMetadata:
    try:
        metadata = get_uploaded_object_metadata(payload.input_object_key)
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

    if metadata.content_length <= 0:
        raise HTTPException(status_code=400, detail="Uploaded object has invalid size")

    if metadata.content_length > MAX_UPLOAD_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400, detail="Uploaded object exceeds the maximum allowed size"
        )

    normalized_content_type = validate_upload_content_type(metadata.content_type)

    if normalized_content_type != payload.content_type:
        raise HTTPException(
            status_code=400,
            detail="Uploaded object content type does not match the job request",
        )

    return metadata


def build_job_response(
    row: tuple[
        UUID,
        str,
        str,
        str,
        str,
        float | None,
        int | None,
        int | None,
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
    upload_url = generate_presigned_upload_url(
        object_key,
        payload.content_type,
        UPLOAD_URL_EXPIRES_IN_SECONDS,
    )

    return CreateUploadUrlResponse(
        object_key=object_key,
        upload_url=upload_url,
        expires_in_seconds=UPLOAD_URL_EXPIRES_IN_SECONDS,
    )


@app.post("/jobs", response_model=JobResponse)
def create_job(payload: CreateJobRequest) -> JobResponse:
    validate_uploaded_object_for_job(payload)

    with psycopg.connect(get_database_url()) as conn:
        with conn.cursor() as cur:
            job_id = uuid4()
            cur.execute(
                """
                INSERT INTO analysis_jobs (
                    id,
                    status,
                    original_filename,
                    content_type,
                    input_object_key
                )
                VALUES (%s, %s, %s, %s, %s)
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
                ),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="Failed to create job")

    try:
        get_job_queue().enqueue(process_analysis_job, str(job_id))
    except Exception as error:
        raise HTTPException(status_code=502, detail="Failed to enqueue job") from error

    return build_job_response(row)


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID) -> JobResponse:
    with psycopg.connect(get_database_url()) as conn:
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
