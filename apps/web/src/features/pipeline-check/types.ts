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

export type AnalysisResult = {
  normalization: AnalysisNormalizationResult
  original_video: ProbedVideoMetadata
  analysis_video: ProbedVideoMetadata
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
