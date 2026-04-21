from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException

from app.api.jobs import (
    build_job_response_from_row,
    get_job_row_by_id,
    insert_job_and_return_row,
    mark_job_as_failed_and_return_row,
)
from app.api.schemas import (
    CreateJobRequest,
    CreateUploadUrlRequest,
    CreateUploadUrlResponse,
    JobResponse,
)
from app.api.upload_validation import validate_uploaded_object_for_job
from app.services.r2_storage import (
    build_upload_object_key,
    generate_presigned_upload_url,
)
from app.workers.job_queue import get_job_queue
from app.workers.tasks import process_analysis_job

UPLOAD_URL_EXPIRES_IN_SECONDS = 900

app = FastAPI()


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

    job_id = uuid4()
    row = insert_job_and_return_row(job_id, payload)

    if row is None:
        raise HTTPException(status_code=500, detail="Failed to create job")

    try:
        get_job_queue().enqueue(process_analysis_job, str(job_id))
    except Exception as error:
        row = mark_job_as_failed_and_return_row(job_id, "Failed to enqueue job")

        raise HTTPException(
            status_code=502,
            detail=build_job_response_from_row(row).model_dump(),
        ) from error

    return build_job_response_from_row(row)


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID) -> JobResponse:
    row = get_job_row_by_id(job_id)

    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return build_job_response_from_row(row)
