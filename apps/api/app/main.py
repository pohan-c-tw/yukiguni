from typing import Any
from uuid import UUID, uuid4

import psycopg
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from psycopg.rows import namedtuple_row

from app.job_queue import get_job_queue
from app.r2_storage import (
    UploadedObjectMetadata,
    build_upload_object_key,
    generate_presigned_upload_url,
    get_uploaded_object_metadata,
)
from app.schemas import (
    CreateJobRequest,
    CreateUploadUrlRequest,
    CreateUploadUrlResponse,
    JobResponse,
)
from app.settings import get_database_url
from app.tasks import process_analysis_job
from app.validation import MAX_UPLOAD_FILE_SIZE_BYTES, validate_upload_content_type

app = FastAPI()

UPLOAD_URL_EXPIRES_IN_SECONDS = 900


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
    row: Any,
) -> JobResponse:
    return JobResponse(
        id=row.id,
        status=row.status,
        original_filename=row.original_filename,
        content_type=row.content_type,
        input_object_key=row.input_object_key,
        video_duration_seconds=row.video_duration_seconds,
        video_width=row.video_width,
        video_height=row.video_height,
        error_message=row.error_message,
        processing_started_at=row.processing_started_at,
        completed_at=row.completed_at,
        failed_at=row.failed_at,
    )


def mark_job_as_failed(job_id: UUID, error_message: str) -> Any:
    with psycopg.connect(get_database_url(), row_factory=namedtuple_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE analysis_jobs
                SET
                    status = %s,
                    error_message = %s,
                    failed_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                RETURNING
                    id,
                    status,
                    original_filename,
                    content_type,
                    input_object_key,
                    video_duration_seconds,
                    video_width,
                    video_height,
                    error_message,
                    processing_started_at,
                    completed_at,
                    failed_at
                """,
                ("failed", error_message, job_id),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to update job failure state",
        )

    return row


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

    with psycopg.connect(get_database_url(), row_factory=namedtuple_row) as conn:
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
                    error_message,
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
        row = mark_job_as_failed(job_id, "Failed to enqueue job")
        raise HTTPException(
            status_code=502,
            detail=build_job_response(row).model_dump(),
        ) from error

    return build_job_response(row)


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID) -> JobResponse:
    with psycopg.connect(get_database_url(), row_factory=namedtuple_row) as conn:
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
                    error_message,
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
