import type {
  AnalysisJobResponse,
  CreateJobRequest,
  CreatePresignedUploadUrlRequest,
  CreatePresignedUploadUrlResponse,
} from '@/features/pipeline-check/types'
import { API_BASE_URL } from '@/lib/config'

async function parseErrorMessage(response: Response): Promise<string> {
  const fallbackMessage = `Request failed with status ${response.status}`

  try {
    const payload: unknown = await response.json()

    // Supported FastAPI error shapes:
    // - { detail: "Message" }
    // - { detail: { message: "Message", ...debugFields } }
    // Other detail shapes, including validation errors, fall back to JSON.
    if (!payload || typeof payload !== 'object' || !('detail' in payload)) {
      return fallbackMessage
    }

    const { detail } = payload

    if (typeof detail === 'string') {
      return detail
    }

    if (
      detail &&
      typeof detail === 'object' &&
      !Array.isArray(detail) &&
      'message' in detail &&
      typeof detail.message === 'string'
    ) {
      return detail.message
    }

    return JSON.stringify(detail)
  } catch {
    return fallbackMessage
  }
}

export async function createPresignedUploadUrl(
  payload: CreatePresignedUploadUrlRequest,
): Promise<CreatePresignedUploadUrlResponse> {
  const response = await fetch(`${API_BASE_URL}/uploads/presign`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

export async function uploadFileToR2(
  uploadUrl: string,
  file: File,
): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: {
      'Content-Type': file.type,
    },
    body: file,
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
}

export async function createJob(
  payload: CreateJobRequest,
): Promise<AnalysisJobResponse> {
  const response = await fetch(`${API_BASE_URL}/jobs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}

export async function fetchJob(jobId: string): Promise<AnalysisJobResponse> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`)

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}
