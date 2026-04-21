import psycopg
from psycopg.rows import namedtuple_row

from app.core.job_status import JobStatus
from app.core.settings import get_database_url
from app.services.video_probe import ProbedVideoMetadata


def get_job_input_object_key_by_id(job_id: str) -> str:
    with psycopg.connect(get_database_url(), row_factory=namedtuple_row) as conn:
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

    return row.input_object_key


def update_job_to_processing(job_id: str) -> None:
    with psycopg.connect(get_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE analysis_jobs
                SET
                    status = %s,
                    processing_started_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (JobStatus.PROCESSING, job_id),
            )


def update_job_to_done(job_id: str, probed_video: ProbedVideoMetadata) -> None:
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
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    JobStatus.DONE,
                    probed_video.duration_seconds,
                    probed_video.width,
                    probed_video.height,
                    job_id,
                ),
            )


def update_job_to_failed(job_id: str, error_message: str) -> None:
    with psycopg.connect(get_database_url()) as conn:
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
                """,
                (JobStatus.FAILED, error_message, job_id),
            )
