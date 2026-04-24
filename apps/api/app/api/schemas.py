from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.api.validation import (
    validate_filename_like,
    validate_upload_content_type,
    validate_upload_file_size,
    validate_upload_object_key,
)
from app.core.job_status import JobStatus


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
    def validate_content_type(cls, value: str) -> str:
        return validate_upload_content_type(value)

    @field_validator("input_object_key")
    @classmethod
    def validate_input_object_key(cls, value: str) -> str:
        return validate_upload_object_key(value)


class JobResponse(BaseModel):
    id: UUID
    status: JobStatus
    original_filename: str
    content_type: str
    input_object_key: str
    video_duration_seconds: float | None
    video_width: int | None
    video_height: int | None
    error_message: str | None
    processing_started_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None
