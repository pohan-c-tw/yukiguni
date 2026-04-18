import os
from uuid import uuid4

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI()


class CreateJobRequest(BaseModel):
    input_object_key: str


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return database_url


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, str]:
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, input_object_key
                FROM analysis_jobs
                WHERE id = %s
                """,
                (job_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": str(row[0]),
        "status": row[1],
        "input_object_key": row[2],
    }


@app.post("/jobs")
def create_job(payload: CreateJobRequest) -> dict[str, str]:
    job_id = str(uuid4())
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO analysis_jobs (id, status, input_object_key)
                VALUES (%s, %s, %s)
                RETURNING id, status, input_object_key
                """,
                (job_id, "uploaded", payload.input_object_key),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="Failed to create job")

    return {
        "id": str(row[0]),
        "status": row[1],
        "input_object_key": row[2],
    }
