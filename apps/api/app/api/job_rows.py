from typing import Any, Mapping
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from app.api.schemas import AnalysisJobResponse, CreateJobRequest
from app.core.job_status import JobStatus
from app.core.settings import get_database_url

ANALYSIS_JOB_RESPONSE_COLUMNS = """
    id,
    status,
    original_filename,
    content_type,
    input_object_key,
    video_duration_seconds,
    video_width,
    video_height,
    analysis_result,
    error_message,
    processing_started_at,
    completed_at,
    failed_at
"""
SELECT_ANALYSIS_JOB_RESPONSE_SQL = (
    "SELECT" + ANALYSIS_JOB_RESPONSE_COLUMNS + "\nFROM analysis_jobs"
)


def create_analysis_job_row(
    job_id: UUID,
    payload: CreateJobRequest,
) -> Mapping[str, Any] | None:
    with psycopg.connect(get_database_url(), row_factory=dict_row) as conn:
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
                + ANALYSIS_JOB_RESPONSE_COLUMNS,
                (
                    job_id,
                    JobStatus.UPLOADED,
                    payload.original_filename,
                    payload.content_type,
                    payload.input_object_key,
                ),
            )
            return cur.fetchone()


def get_job_response_row_by_id(job_id: UUID) -> Mapping[str, Any] | None:
    with psycopg.connect(get_database_url(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                SELECT_ANALYSIS_JOB_RESPONSE_SQL
                + """
                WHERE id = %s
                """,
                (job_id,),
            )
            return cur.fetchone()


def row_to_analysis_job_response(
    row: Mapping[str, Any],
) -> AnalysisJobResponse:
    return AnalysisJobResponse.model_validate(row)


def mark_job_enqueue_failed(
    job_id: UUID, error_message: str
) -> Mapping[str, Any] | None:
    with psycopg.connect(get_database_url(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE analysis_jobs
                SET
                    status = %s,
                    output_object_key = NULL,
                    video_duration_seconds = NULL,
                    video_width = NULL,
                    video_height = NULL,
                    analysis_result = NULL,
                    error_message = %s,
                    processing_started_at = NULL,
                    completed_at = NULL,
                    failed_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                  AND status = %s
                RETURNING
                """
                + ANALYSIS_JOB_RESPONSE_COLUMNS,
                (JobStatus.FAILED, error_message, job_id, JobStatus.UPLOADED),
            )
            return cur.fetchone()
