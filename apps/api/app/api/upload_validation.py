from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.api.schemas import CreateJobRequest
from app.api.validation import (
    MAX_UPLOAD_FILE_SIZE_BYTES,
    validate_upload_content_type,
)
from app.services.r2_storage import UploadedObjectMetadata, get_uploaded_object_metadata


def validate_uploaded_object_for_job(
    payload: CreateJobRequest,
) -> UploadedObjectMetadata:
    try:
        metadata = get_uploaded_object_metadata(payload.input_object_key)
    except ClientError as error:
        status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        error_code = error.response.get("Error", {}).get("Code")

        if status_code == 404 or error_code in {
            "404",
            "NotFound",
            "NoSuchKey",
        }:
            raise HTTPException(
                status_code=400,
                detail="Uploaded object not found",
            ) from error

        raise HTTPException(
            status_code=502,
            detail="Failed to read uploaded object metadata",
        ) from error

    if metadata.content_length <= 0:
        raise HTTPException(status_code=400, detail="Uploaded object has invalid size")

    if metadata.content_length > MAX_UPLOAD_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="Uploaded object exceeds the maximum allowed size",
        )

    try:
        normalized_content_type = validate_upload_content_type(metadata.content_type)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail="Uploaded object has unsupported content type",
        ) from error

    if normalized_content_type != payload.content_type:
        raise HTTPException(
            status_code=400,
            detail="Uploaded object content type does not match the job request",
        )

    return metadata
