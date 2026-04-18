import os
from typing import Literal
from uuid import UUID, uuid4

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI()


class CreateJobRequest(BaseModel):
    input_object_key: str


class JobResponse(BaseModel):
    id: UUID
    status: Literal["uploaded", "processing", "done", "failed"]
    input_object_key: str


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return database_url


def build_job_response(row: tuple[UUID, str, str]) -> JobResponse:
    return JobResponse(
        id=row[0],
        status=row[1],
        input_object_key=row[2],
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID) -> JobResponse:
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

    return build_job_response(row)


@app.post("/jobs", response_model=JobResponse)
def create_job(payload: CreateJobRequest) -> JobResponse:
    job_id = uuid4()
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

    return build_job_response(row)
