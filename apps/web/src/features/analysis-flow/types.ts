export type StepKey = 'presign' | 'upload' | 'create-job'

export type StepStatus = 'idle' | 'running' | 'success' | 'failed'

export type StepState = {
  status: StepStatus
  error: string | null
}
export type StepStates = Record<StepKey, StepState>

export type JobStatus =
  | 'uploaded'
  | 'validating'
  | 'processing'
  | 'done'
  | 'failed'

export type UploadUrlRequest = {
  filename: string
  content_type: string
  file_size: number
}

export type UploadUrlResponse = {
  object_key: string
  upload_url: string
  expires_in_seconds: number
}

export type CreateJobRequest = {
  original_filename: string
  content_type: string
  input_object_key: string
}

export type JobResponse = {
  id: string
  status: JobStatus
  original_filename: string
  content_type: string
  input_object_key: string
  video_duration_seconds: number | null
  video_width: number | null
  video_height: number | null
  error_message: string | null
  processing_started_at: string | null
  completed_at: string | null
  failed_at: string | null
}
