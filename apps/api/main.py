import os
from typing import Literal
from uuid import UUID, uuid4

import boto3
import psycopg
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


def build_job_response(row: tuple[UUID, str, str, str, str]) -> JobResponse:
    return JobResponse(
        id=row[0],
        status=row[1],
        original_filename=row[2],
        content_type=row[3],
        input_object_key=row[4],
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
                    input_object_key
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, status, original_filename, content_type, input_object_key
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

    return build_job_response(row)


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID) -> JobResponse:
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, original_filename, content_type, input_object_key
                FROM analysis_jobs
                WHERE id = %s
                """,
                (job_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return build_job_response(row)
