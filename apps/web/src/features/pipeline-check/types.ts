export type StepStatus = 'idle' | 'running' | 'success' | 'failed'

export type StepState = {
  status: StepStatus
  error: string | null
}

export type ClientStage = {
  label: string
  description: string
  detailLabel: string
  detailValue: string | null
  state: StepState
}

export type JobStatus =
  | 'uploaded'
  | 'validating'
  | 'processing'
  | 'done'
  | 'failed'

export type CreatePresignedUploadUrlRequest = {
  filename: string
  content_type: string
  file_size: number
}

export type CreatePresignedUploadUrlResponse = {
  object_key: string
  upload_url: string
  expires_in_seconds: number
}

export type AnalysisVideoUrlResponse = {
  object_key: string
  video_url: string
  expires_in_seconds: number
}

export type CreateJobRequest = {
  original_filename: string
  content_type: string
  input_object_key: string
}

export type ProbedVideoMetadata = {
  duration_seconds: number
  width: number
  height: number
  fps: number | null
  codec_name: string | null
  rotation_degrees: number | null
}

export type AnalysisNormalizationResult = {
  enabled: boolean
  timing_mode: string
  target_fps: number
  max_long_edge: number
  stored_object_key: string | null
}

export type PoseLandmarksVideoMetadata = {
  fps: number | null
  frame_count: number
  width: number
  height: number
}

export type PoseLandmark = {
  x: number
  y: number
  z: number
  visibility: number
}

export type PoseLandmarkFrame = {
  frame_index: number
  timestamp_ms: number
  pose_detected: boolean
  landmarks: Record<string, PoseLandmark>
}

export type PoseDetectionResult = {
  model: string
  model_asset_name: string | null
  landmark_format: string
  detected_frame_count: number
  frames: PoseLandmarkFrame[]
}

export type PoseLandmarksResult = {
  schema_version: string
  video: PoseLandmarksVideoMetadata
  pose: PoseDetectionResult
}

export type GaitAnalysisResult = {
  schema_version: string
}

export type AnalysisResult = {
  schema_version: string | null
  normalization: AnalysisNormalizationResult
  original_video: ProbedVideoMetadata
  analysis_video: ProbedVideoMetadata
  pose_landmarks: PoseLandmarksResult | null
  gait: GaitAnalysisResult | null
}

export type AnalysisJobResponse = {
  id: string
  status: JobStatus
  original_filename: string
  content_type: string
  input_object_key: string
  video_duration_seconds: number | null
  video_width: number | null
  video_height: number | null
  analysis_result: AnalysisResult | null
  error_message: string | null
  processing_started_at: string | null
  completed_at: string | null
  failed_at: string | null
}
