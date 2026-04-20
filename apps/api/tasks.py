import os

import psycopg
from botocore.exceptions import ClientError
from psycopg.rows import tuple_row

from r2_storage import download_uploaded_object_to_tempfile
from settings import get_database_url
from video_probe import ProbedVideoMetadata, probe_video_file


def get_job_input_object_key(job_id: str) -> str:
    with psycopg.connect(get_database_url(), row_factory=tuple_row) as conn:
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

    return row[0]


def mark_job_as_processing(job_id: str) -> None:
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
                ("processing", job_id),
            )


def mark_job_as_done(job_id: str, probed_video: ProbedVideoMetadata) -> None:
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
                    "done",
                    probed_video.duration_seconds,
                    probed_video.width,
                    probed_video.height,
                    job_id,
                ),
            )


def mark_job_as_failed(job_id: str, error_message: str) -> None:
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
                ("failed", error_message, job_id),
            )


def process_analysis_job(job_id: str) -> None:
    temp_file_path = None

    try:
        mark_job_as_processing(job_id)
        input_object_key = get_job_input_object_key(job_id)
        temp_file_path = download_uploaded_object_to_tempfile(input_object_key)
        probed_video = probe_video_file(temp_file_path)
        mark_job_as_done(job_id, probed_video)
        print(f"Processed analysis job: {job_id}")
    except (ClientError, RuntimeError, ValueError) as error:
        mark_job_as_failed(job_id, str(error))
        raise
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
