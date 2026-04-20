import psycopg

from settings import get_required_env


def get_database_url() -> str:
    return get_required_env("DATABASE_URL")


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


def process_analysis_job(job_id: str) -> None:
    mark_job_as_processing(job_id)
    print(f"Processing analysis job: {job_id}")
