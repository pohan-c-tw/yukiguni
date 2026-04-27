import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.core.job_status import JobStatus
from app.core.settings import get_database_url
from app.services.analysis_results import AnalysisResult
from app.services.video_probe import ProbedVideoMetadata


class JobStateTransitionError(RuntimeError):
    pass


def get_job_status_by_id(job_id: str) -> JobStatus:
    with psycopg.connect(get_database_url(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status
                FROM analysis_jobs
                WHERE id = %s
                """,
                (job_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise RuntimeError("Job not found")

    return JobStatus(row["status"])


def get_job_input_object_key_by_id(job_id: str) -> str:
    with psycopg.connect(get_database_url(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT input_object_key
                FROM analysis_jobs
                WHERE id = %s
                """,
                (job_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise RuntimeError("Job not found")

    return row["input_object_key"]


def update_job_to_processing(job_id: str) -> None:
    with psycopg.connect(get_database_url()) as conn:
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
                    error_message = NULL,
                    processing_started_at = NOW(),
                    completed_at = NULL,
                    failed_at = NULL,
                    updated_at = NOW()
                WHERE id = %s
                  AND status = %s
                """,
                (JobStatus.PROCESSING, job_id, JobStatus.UPLOADED),
            )
            updated_rows = cur.rowcount

    if updated_rows != 1:
        current_status = get_job_status_by_id(job_id)

        if current_status is JobStatus.PROCESSING:
            raise JobStateTransitionError("Job is already being processed")

        if current_status is JobStatus.DONE:
            raise JobStateTransitionError("Job is already completed")

        if current_status is JobStatus.FAILED:
            raise JobStateTransitionError("Job has already failed")

        raise JobStateTransitionError(
            f"Job cannot transition from {current_status} to processing"
        )


def update_job_to_done(
    job_id: str,
    probed_video: ProbedVideoMetadata,
    analysis_result: AnalysisResult,
) -> None:
    with psycopg.connect(get_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE analysis_jobs
                SET
                    status = %s,
                    video_duration_seconds = %s,
                    video_width = %s,
                    video_height = %s,
                    analysis_result = %s,
                    error_message = NULL,
                    completed_at = NOW(),
                    failed_at = NULL,
                    updated_at = NOW()
                WHERE id = %s
                  AND status = %s
                """,
                (
                    JobStatus.DONE,
                    probed_video.duration_seconds,
                    probed_video.width,
                    probed_video.height,
                    Jsonb(analysis_result.model_dump()),
                    job_id,
                    JobStatus.PROCESSING,
                ),
            )
            updated_rows = cur.rowcount

    if updated_rows != 1:
        current_status = get_job_status_by_id(job_id)
        raise JobStateTransitionError(
            f"Job cannot transition from {current_status} to done"
        )


def update_job_to_failed(job_id: str, error_message: str) -> None:
    with psycopg.connect(get_database_url()) as conn:
        with conn.cursor() as cur:
            # Keep processing_started_at to show when the worker began processing.
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
                    completed_at = NULL,
                    failed_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                  AND status = %s
                """,
                (JobStatus.FAILED, error_message, job_id, JobStatus.PROCESSING),
            )
            updated_rows = cur.rowcount

    if updated_rows != 1:
        current_status = get_job_status_by_id(job_id)
        raise JobStateTransitionError(
            f"Job cannot transition from {current_status} to failed"
        )
