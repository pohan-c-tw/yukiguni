import time

from app.core.settings import get_pose_model_path
from app.services.analysis_results import build_analysis_result
from app.services.pose_landmarks import detect_pose_landmarks
from app.services.r2_storage import (
    build_analysis_video_object_key,
    download_uploaded_object_to_tempfile,
    upload_analysis_video_file,
)
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


def format_logfmt_value(value: object) -> str:
    text = str(value)

    if not text:
        return '""'

    if any(character.isspace() or character == '"' for character in text):
        escaped_text = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped_text}"'

    return text


def log_analysis_job_event(
    job_id: str,
    event: str,
    started_at: float,
    **fields: object,
) -> None:
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    log_fields = {
        "event": event,
        "job_id": job_id,
        "elapsed_ms": elapsed_ms,
        **fields,
    }
    formatted_fields = " ".join(
        f"{key}={format_logfmt_value(value)}" for key, value in log_fields.items()
    )
    print(f"analysis_job {formatted_fields}")


def process_analysis_job(job_id: str) -> None:
    started_at = time.perf_counter()
    temp_file_path = None
    normalized_file_path = None

    log_analysis_job_event(job_id, "started", started_at)

    try:
        update_job_to_processing(job_id)
    except JobStateTransitionError as error:
        log_analysis_job_event(
            job_id,
            "claim_skipped",
            started_at,
            error=error,
        )
        return

    try:
        log_analysis_job_event(job_id, "input_lookup_started", started_at)
        input_object_key = get_job_input_object_key_by_id(job_id)
        log_analysis_job_event(
            job_id,
            "input_lookup_finished",
            started_at,
            input_object_key=input_object_key,
        )

        log_analysis_job_event(job_id, "download_started", started_at)
        temp_file_path = download_uploaded_object_to_tempfile(input_object_key)
        log_analysis_job_event(job_id, "download_finished", started_at)

        log_analysis_job_event(job_id, "probe_original_started", started_at)
        probed_video_metadata = probe_video_file(temp_file_path)
        log_analysis_job_event(
            job_id,
            "probe_original_finished",
            started_at,
            duration_seconds=probed_video_metadata.duration_seconds,
            width=probed_video_metadata.width,
            height=probed_video_metadata.height,
            fps=probed_video_metadata.fps,
        )

        log_analysis_job_event(job_id, "normalize_started", started_at)
        normalized_video_result = normalize_video_for_analysis(
            temp_file_path,
            probed_video_metadata.fps,
        )
        normalized_file_path = normalized_video_result.file_path
        log_analysis_job_event(
            job_id,
            "normalize_finished",
            started_at,
            target_fps=normalized_video_result.target_fps,
            width=normalized_video_result.metadata.width,
            height=normalized_video_result.metadata.height,
            fps=normalized_video_result.metadata.fps,
        )

        analysis_video_object_key = build_analysis_video_object_key(job_id)
        log_analysis_job_event(
            job_id,
            "analysis_video_upload_started",
            started_at,
            object_key=analysis_video_object_key,
        )
        upload_analysis_video_file(normalized_file_path, analysis_video_object_key)
        log_analysis_job_event(
            job_id,
            "analysis_video_upload_finished",
            started_at,
            object_key=analysis_video_object_key,
        )

        log_analysis_job_event(job_id, "pose_started", started_at)
        pose_landmarks = detect_pose_landmarks(
            normalized_file_path,
            normalized_video_result.metadata,
            get_pose_model_path(),
        )
        log_analysis_job_event(
            job_id,
            "pose_finished",
            started_at,
            frames=len(pose_landmarks.pose.frames),
            detected_frames=pose_landmarks.pose.detected_frame_count,
        )

        log_analysis_job_event(job_id, "analysis_result_build_started", started_at)
        analysis_result = build_analysis_result(
            probed_video_metadata,
            analysis_video_object_key,
            normalized_video_result,
            pose_landmarks,
        )
        log_analysis_job_event(job_id, "analysis_result_build_finished", started_at)

        log_analysis_job_event(job_id, "db_update_done_started", started_at)
        update_job_to_done(job_id, probed_video_metadata, analysis_result)
        log_analysis_job_event(job_id, "done", started_at)
    except Exception as error:
        log_analysis_job_event(
            job_id,
            "failed",
            started_at,
            error=error,
        )
        try:
            update_job_to_failed(job_id, str(error))
        except JobStateTransitionError as transition_error:
            log_analysis_job_event(
                job_id,
                "failure_update_skipped",
                started_at,
                error=transition_error,
            )
        except Exception as failure_update_error:
            log_analysis_job_event(
                job_id,
                "failure_update_failed",
                started_at,
                error=failure_update_error,
            )
        raise
    finally:
        log_analysis_job_event(job_id, "cleanup_started", started_at)
        remove_file_if_exists(temp_file_path)
        remove_file_if_exists(normalized_file_path)
        log_analysis_job_event(job_id, "cleanup_finished", started_at)
