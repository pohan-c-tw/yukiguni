from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import RedisError

from app.api.job_rows import (
    create_analysis_job_row,
    get_job_response_row_by_id,
    mark_job_enqueue_failed,
    row_to_analysis_job_response,
)
from app.api.schemas import (
    AnalysisJobResponse,
    CreateJobRequest,
    CreatePresignedUploadUrlRequest,
    CreatePresignedUploadUrlResponse,
)
from app.api.upload_validation import validate_uploaded_object_for_job
from app.core.settings import SettingsError, get_cors_allow_origins
from app.services.r2_storage import (
    build_upload_object_key,
    generate_presigned_upload_url,
)
from app.workers.job_queue import get_job_queue
from app.workers.tasks import process_analysis_job

UPLOAD_URL_EXPIRES_IN_SECONDS = 15 * 60

app = FastAPI()

cors_allow_origins = get_cors_allow_origins()

if cors_allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        allow_credentials=False,
    )


@app.get("/healthz")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/uploads/presign", response_model=CreatePresignedUploadUrlResponse)
def create_presigned_upload_url(
    payload: CreatePresignedUploadUrlRequest,
) -> CreatePresignedUploadUrlResponse:
    object_key = build_upload_object_key(payload.filename)

    try:
        upload_url = generate_presigned_upload_url(
            object_key,
            payload.content_type,
            UPLOAD_URL_EXPIRES_IN_SECONDS,
        )
    except SettingsError as error:
        raise HTTPException(
            status_code=500,
            detail="Upload URL service is not configured",
        ) from error
    except (BotoCoreError, ClientError) as error:
        raise HTTPException(
            status_code=502,
            detail="Failed to create upload URL",
        ) from error

    return CreatePresignedUploadUrlResponse(
        object_key=object_key,
        upload_url=upload_url,
        expires_in_seconds=UPLOAD_URL_EXPIRES_IN_SECONDS,
    )


def ensure_job_marked_enqueue_failed(job_id: UUID, error: Exception) -> None:
    try:
        row = mark_job_enqueue_failed(job_id, "Failed to enqueue job")
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to update job failure state",
        ) from error

    if row is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to update job failure state",
        ) from error


@app.post("/jobs", response_model=AnalysisJobResponse)
def create_job(payload: CreateJobRequest) -> AnalysisJobResponse:
    validate_uploaded_object_for_job(payload)

    job_id = uuid4()
    row = create_analysis_job_row(job_id, payload)

    if row is None:
        raise HTTPException(status_code=500, detail="Failed to create job")

    try:
        get_job_queue().enqueue(process_analysis_job, str(job_id))
    except SettingsError as error:
        ensure_job_marked_enqueue_failed(job_id, error)

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Queue service is not configured",
                "job_id": str(job_id),
            },
        ) from error
    except RedisError as error:
        ensure_job_marked_enqueue_failed(job_id, error)

        raise HTTPException(
            status_code=502,
            detail={
                "message": "Failed to enqueue job",
                "job_id": str(job_id),
            },
        ) from error
    except Exception as error:
        ensure_job_marked_enqueue_failed(job_id, error)

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to enqueue job",
                "job_id": str(job_id),
            },
        ) from error

    return row_to_analysis_job_response(row)


@app.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
def get_job(job_id: UUID) -> AnalysisJobResponse:
    row = get_job_response_row_by_id(job_id)

    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return row_to_analysis_job_response(row)
