from botocore.exceptions import ClientError

from app.services.analysis_results import build_analysis_result
from app.services.r2_storage import download_uploaded_object_to_tempfile
from app.services.temp_files import remove_file_if_exists
from app.services.video_normalize import normalize_video_for_analysis
from app.services.video_probe import probe_video_file
from app.workers.job_state import (
    JobStateTransitionError,
    get_job_input_object_key_by_id,
    update_job_to_done,
    update_job_to_failed,
    update_job_to_processing,
)


def process_analysis_job(job_id: str) -> None:
    temp_file_path = None
    normalized_file_path = None

    try:
        update_job_to_processing(job_id)
    except JobStateTransitionError as error:
        print(f"Skipped analysis job {job_id}: {error}")
        return

    try:
        input_object_key = get_job_input_object_key_by_id(job_id)
        temp_file_path = download_uploaded_object_to_tempfile(input_object_key)
        probed_video_metadata = probe_video_file(temp_file_path)
        normalized_video_result = normalize_video_for_analysis(
            temp_file_path,
            probed_video_metadata.fps,
        )
        normalized_file_path = normalized_video_result.file_path
        analysis_result = build_analysis_result(
            probed_video_metadata, normalized_video_result
        )
        update_job_to_done(job_id, probed_video_metadata, analysis_result)
        print(f"Processed analysis job: {job_id}")
    except (ClientError, RuntimeError, ValueError) as error:
        try:
            update_job_to_failed(job_id, str(error))
        except JobStateTransitionError as transition_error:
            print(
                f"Skipped failure update for analysis job {job_id}: {transition_error}"
            )
        raise
    finally:
        remove_file_if_exists(temp_file_path)
        remove_file_if_exists(normalized_file_path)
