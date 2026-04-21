import os

from botocore.exceptions import ClientError

from app.services.r2_storage import download_uploaded_object_to_tempfile
from app.services.video_probe import probe_video_file
from app.workers.jobs import (
    get_job_input_object_key,
    mark_job_as_done,
    mark_job_as_failed,
    mark_job_as_processing,
)


def cleanup_temp_file(file_path: str | None) -> None:
    if file_path and os.path.exists(file_path):
        os.unlink(file_path)


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
        cleanup_temp_file(temp_file_path)
