from pathlib import Path
from typing import Any

from app.services.analysis_results import (
    POSE_LANDMARK_FORMAT,
    POSE_LANDMARKS_SCHEMA_VERSION,
    POSE_MODEL_ASSET_NAME,
    POSE_MODEL_NAME,
    PoseDetectionResult,
    PoseLandmarkFrame,
    PoseLandmarksResult,
    PoseLandmarksVideoMetadata,
)
from app.services.video_probe import ProbedVideoMetadata

POSE_LANDMARK_NAMES = [
    "nose",
    "left_eye_inner",
    "left_eye",
    "left_eye_outer",
    "right_eye_inner",
    "right_eye",
    "right_eye_outer",
    "left_ear",
    "right_ear",
    "mouth_left",
    "mouth_right",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_pinky",
    "right_pinky",
    "left_index",
    "right_index",
    "left_thumb",
    "right_thumb",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
    "left_heel",
    "right_heel",
    "left_foot_index",
    "right_foot_index",
]


def detect_pose_landmarks(
    analysis_video_path: str,
    analysis_video_metadata: ProbedVideoMetadata,
    model_path: Path,
) -> PoseLandmarksResult:
    if not model_path.exists():
        raise FileNotFoundError(f"Pose Landmarker model file not found: {model_path}")

    if analysis_video_metadata.fps is None or analysis_video_metadata.fps <= 0:
        raise ValueError("Analysis video fps is required for MediaPipe VIDEO mode")

    try:
        import cv2
        import mediapipe as mp
    except ImportError as error:
        raise RuntimeError(
            "MediaPipe pose detection dependencies are not available"
        ) from error

    frames: list[PoseLandmarkFrame] = []
    capture = cv2.VideoCapture(analysis_video_path)

    if not capture.isOpened():
        raise ValueError("Analysis video could not be opened for pose detection")

    try:
        base_options = mp.tasks.BaseOptions(model_asset_path=str(model_path))
        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
        )

        with mp.tasks.vision.PoseLandmarker.create_from_options(options) as landmarker:
            frame_index = 0

            while True:
                frame_was_read, bgr_frame = capture.read()

                if not frame_was_read:
                    break

                timestamp_ms = int((frame_index / analysis_video_metadata.fps) * 1000)

                rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                result = landmarker.detect_for_video(mp_image, timestamp_ms)
                landmarks = extract_pose_landmarks(result)

                frames.append(
                    PoseLandmarkFrame(
                        frame_index=frame_index,
                        timestamp_ms=timestamp_ms,
                        pose_detected=bool(landmarks),
                        landmarks=landmarks,
                    )
                )
                frame_index += 1
    finally:
        capture.release()

    return PoseLandmarksResult(
        schema_version=POSE_LANDMARKS_SCHEMA_VERSION,
        video=PoseLandmarksVideoMetadata(
            fps=analysis_video_metadata.fps,
            frame_count=len(frames),
            width=analysis_video_metadata.width,
            height=analysis_video_metadata.height,
        ),
        pose=PoseDetectionResult(
            model=POSE_MODEL_NAME,
            model_asset_name=POSE_MODEL_ASSET_NAME,
            landmark_format=POSE_LANDMARK_FORMAT,
            detected_frame_count=sum(1 for frame in frames if frame.pose_detected),
            frames=frames,
        ),
    )


def extract_pose_landmarks(result: Any) -> dict[str, dict[str, float]]:
    if not result.pose_landmarks:
        return {}

    pose_landmarks = result.pose_landmarks[0]

    if len(pose_landmarks) != len(POSE_LANDMARK_NAMES):
        raise RuntimeError(
            "Unexpected number of pose landmarks returned by MediaPipe. "
            f"Expected {len(POSE_LANDMARK_NAMES)}, got {len(pose_landmarks)}."
        )

    return {
        landmark_name: {
            "x": float(landmark.x),
            "y": float(landmark.y),
            "z": float(landmark.z),
            "visibility": float(landmark.visibility),
        }
        for landmark_name, landmark in zip(
            POSE_LANDMARK_NAMES, pose_landmarks, strict=True
        )
    }
