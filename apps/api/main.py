import os
from typing import Literal
from uuid import UUID, uuid4

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI()


class CreateUploadUrlRequest(BaseModel):
    filename: str
    content_type: str


class CreateUploadUrlResponse(BaseModel):
    object_key: str
    upload_url: str
    expires_in_seconds: int


class CreateJobRequest(BaseModel):
    input_object_key: str


class JobResponse(BaseModel):
    id: UUID
    status: Literal["uploaded", "processing", "done", "failed"]
    input_object_key: str


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return database_url


def build_upload_object_key(filename: str) -> str:
    return f"uploads/{uuid4()}-{filename}"


def build_job_response(row: tuple[UUID, str, str]) -> JobResponse:
    return JobResponse(
        id=row[0],
        status=row[1],
        input_object_key=row[2],
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/uploads/presign", response_model=CreateUploadUrlResponse)
def create_upload_url(payload: CreateUploadUrlRequest) -> CreateUploadUrlResponse:
    object_key = build_upload_object_key(payload.filename)

    # This is a placeholder until we integrate Cloudflare R2 presigned uploads.
    upload_url = f"https://example-upload-url.local/{object_key}"

    return CreateUploadUrlResponse(
        object_key=object_key,
        upload_url=upload_url,
        expires_in_seconds=900,
    )


@app.post("/jobs", response_model=JobResponse)
def create_job(payload: CreateJobRequest) -> JobResponse:
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            job_id = uuid4()
            cur.execute(
                """
                INSERT INTO analysis_jobs (id, status, input_object_key)
                VALUES (%s, %s, %s)
                RETURNING id, status, input_object_key
                """,
                (job_id, "uploaded", payload.input_object_key),
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
                SELECT id, status, input_object_key
                FROM analysis_jobs
                WHERE id = %s
                """,
                (job_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return build_job_response(row)
