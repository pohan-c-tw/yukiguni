import os
import tempfile
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel

from settings import get_required_env


class R2Settings(BaseModel):
    bucket_name: str
    access_key_id: str
    secret_access_key: str
    endpoint: str


class UploadedObjectMetadata(BaseModel):
    content_length: int
    content_type: str


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


def generate_presigned_upload_url(
    object_key: str,
    content_type: str,
    expires_in: int,
) -> str:
    settings = get_r2_settings()
    r2_client = create_r2_client()

    return r2_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.bucket_name,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )


def get_uploaded_object_metadata(object_key: str) -> UploadedObjectMetadata:
    settings = get_r2_settings()
    r2_client = create_r2_client()
    response = r2_client.head_object(
        Bucket=settings.bucket_name,
        Key=object_key,
    )

    return UploadedObjectMetadata(
        content_length=response["ContentLength"],
        content_type=response["ContentType"],
    )


def download_uploaded_object_to_tempfile(object_key: str) -> str:
    settings = get_r2_settings()
    r2_client = create_r2_client()
    _, suffix = os.path.splitext(object_key)

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file_path = temp_file.name

    try:
        with open(temp_file_path, "wb") as file_handle:
            r2_client.download_fileobj(
                Bucket=settings.bucket_name,
                Key=object_key,
                Fileobj=file_handle,
            )
    except ClientError:
        os.unlink(temp_file_path)
        raise

    return temp_file_path
