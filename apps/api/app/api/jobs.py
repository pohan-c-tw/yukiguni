from typing import Any
from uuid import UUID

import psycopg
from fastapi import HTTPException
from psycopg.rows import namedtuple_row

from app.api.schemas import CreateJobRequest, JobResponse
from app.core.job_status import JobStatus
from app.core.settings import get_database_url

JOB_RESPONSE_COLUMNS = """
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
"""
JOB_RESPONSE_SELECT_SQL = "SELECT" + JOB_RESPONSE_COLUMNS + "\nFROM analysis_jobs"


def build_job_response_from_row(
    row: Any,
) -> JobResponse:
    return JobResponse.model_validate(row._asdict())


def insert_job_and_return_row(
    job_id: UUID,
    payload: CreateJobRequest,
) -> Any:
    with psycopg.connect(get_database_url(), row_factory=namedtuple_row) as conn:
        with conn.cursor() as cur:
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
                """
                + JOB_RESPONSE_COLUMNS,
                (
                    job_id,
                    JobStatus.UPLOADED,
                    payload.original_filename,
                    payload.content_type,
                    payload.input_object_key,
                ),
            )
            return cur.fetchone()


def get_job_row_by_id(job_id: UUID) -> Any:
    with psycopg.connect(get_database_url(), row_factory=namedtuple_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                JOB_RESPONSE_SELECT_SQL
                + """
                WHERE id = %s
                """,
                (job_id,),
            )
            return cur.fetchone()


def mark_job_as_failed_and_return_row(job_id: UUID, error_message: str) -> Any:
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
                """
                + JOB_RESPONSE_COLUMNS,
                (JobStatus.FAILED, error_message, job_id),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to update job failure state",
        )

    return row
