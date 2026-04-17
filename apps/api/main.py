from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

jobs: dict[str, dict[str, str]] = {}


class CreateJobRequest(BaseModel):
    input_object_key: str


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, str]:
    job = jobs.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@app.post("/jobs")
def create_job(payload: CreateJobRequest) -> dict[str, str]:
    job_id = str(uuid4())

    job = {
        "id": job_id,
        "status": "uploaded",
        "input_object_key": payload.input_object_key,
    }

    jobs[job_id] = job
    return job
