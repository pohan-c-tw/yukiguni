import type { AnalysisJobResponse } from '@/features/pipeline-check/types'

export function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatDateTime(value: string | null): string {
  if (!value) {
    return 'Pending'
  }

  return new Date(value).toLocaleString()
}

export function formatResolution(job: AnalysisJobResponse): string {
  if (!job.video_width || !job.video_height) {
    return 'Pending'
  }

  return `${job.video_width} x ${job.video_height}`
}
