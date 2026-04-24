import type {
  CreateJobRequest,
  JobResponse,
  UploadUrlRequest,
  UploadUrlResponse,
} from '@/features/analysis-flow/types'
import { API_BASE_URL } from '@/lib/config'

async function parseErrorMessage(response: Response): Promise<string> {
  const fallbackMessage = `Request failed with status ${response.status}`

  try {
    const payload = await response.json()

    if (typeof payload?.detail === 'string') {
      return payload.detail
    }

    if (
      payload?.detail &&
      typeof payload.detail === 'object' &&
      typeof payload.detail.error_message === 'string'
    ) {
      return payload.detail.error_message
    }

    if (payload?.detail && typeof payload.detail === 'object') {
      return JSON.stringify(payload.detail)
    }
  } catch {
    return fallbackMessage
  }

  return fallbackMessage
}

export async function createUploadUrl(
  payload: UploadUrlRequest,
): Promise<UploadUrlResponse> {
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
): Promise<JobResponse> {
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

export async function fetchJob(jobId: string): Promise<JobResponse> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`)

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json()
}
