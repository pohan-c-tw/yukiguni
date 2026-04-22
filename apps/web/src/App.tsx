import { useEffect, useMemo, useState } from 'react'
import type { SyntheticEvent } from 'react'

import styles from './App.module.css'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || 'http://127.0.0.1:8000'
const POLL_INTERVAL_MS = 3000

type JobStatus = 'uploaded' | 'validating' | 'processing' | 'done' | 'failed'

type CreateUploadUrlResponse = {
  object_key: string
  upload_url: string
  expires_in_seconds: number
}

type JobResponse = {
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

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`
  }

  const units = ['KB', 'MB', 'GB']
  let current = value
  let unitIndex = -1

  while (current >= 1024 && unitIndex < units.length - 1) {
    current /= 1024
    unitIndex += 1
  }

  return `${current.toFixed(current >= 10 ? 0 : 1)} ${units[unitIndex]}`
}

function App() {
  const initialJobId =
    new URLSearchParams(window.location.search).get('job_id') ?? ''
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [jobIdInput, setJobIdInput] = useState(initialJobId)
  const [jobId, setJobId] = useState<string | null>(initialJobId || null)
  const [job, setJob] = useState<JobResponse | null>(null)
  const [uploadState, setUploadState] = useState<
    'idle' | 'uploading' | 'creating-job'
  >('idle')
  const [formError, setFormError] = useState<string | null>(null)
  const [jobError, setJobError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) {
      return
    }

    let cancelled = false

    const loadJob = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/jobs/${encodeURIComponent(jobId)}`,
        )

        if (!response.ok) {
          throw new Error(`Failed to fetch job (${response.status})`)
        }

        const payload = (await response.json()) as JobResponse

        if (cancelled) {
          return
        }

        setJob(payload)
        setJobError(null)
      } catch (error) {
        if (cancelled) {
          return
        }

        setJobError(
          error instanceof Error ? error.message : 'Failed to fetch job',
        )
      }
    }

    void loadJob()

    const timer = window.setInterval(() => {
      void loadJob()
    }, POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [jobId])

  const isSubmitting = uploadState !== 'idle'
  const uploadButtonLabel = useMemo(() => {
    if (uploadState === 'uploading') {
      return 'Uploading video...'
    }

    if (uploadState === 'creating-job') {
      return 'Creating analysis job...'
    }

    return 'Upload and start analysis'
  }, [uploadState])

  const statusClassName = useMemo(() => {
    if (!job) {
      return styles.statusBadge
    }

    if (job.status === 'done') {
      return `${styles.statusBadge} ${styles.statusDone}`
    }

    if (job.status === 'failed') {
      return `${styles.statusBadge} ${styles.statusFailed}`
    }

    if (job.status === 'processing' || job.status === 'validating') {
      return `${styles.statusBadge} ${styles.statusProcessing}`
    }

    return styles.statusBadge
  }, [job])

  const syncJobIdToUrl = (nextJobId: string) => {
    const url = new URL(window.location.href)
    url.searchParams.set('job_id', nextJobId)
    window.history.replaceState({}, '', url)
  }

  const handleFileUpload = async (
    event: SyntheticEvent<HTMLFormElement, SubmitEvent>,
  ) => {
    event.preventDefault()

    if (!selectedFile) {
      setFormError('Choose a video file before starting the upload.')
      return
    }

    setFormError(null)
    setJobError(null)
    setJob(null)
    setUploadState('uploading')

    try {
      const presignResponse = await fetch(`${API_BASE_URL}/uploads/presign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: selectedFile.name,
          content_type: selectedFile.type || 'video/mp4',
          file_size: selectedFile.size,
        }),
      })

      if (!presignResponse.ok) {
        throw new Error(`Presign failed (${presignResponse.status})`)
      }

      const presignPayload =
        (await presignResponse.json()) as CreateUploadUrlResponse

      const uploadResponse = await fetch(presignPayload.upload_url, {
        method: 'PUT',
        headers: {
          'Content-Type': selectedFile.type || 'video/mp4',
        },
        body: selectedFile,
      })

      if (!uploadResponse.ok) {
        throw new Error(`R2 upload failed (${uploadResponse.status})`)
      }

      setUploadState('creating-job')

      const createJobResponse = await fetch(`${API_BASE_URL}/jobs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          original_filename: selectedFile.name,
          content_type: selectedFile.type || 'video/mp4',
          input_object_key: presignPayload.object_key,
        }),
      })

      if (!createJobResponse.ok) {
        throw new Error(`Create job failed (${createJobResponse.status})`)
      }

      const createdJob = (await createJobResponse.json()) as JobResponse

      setJob(createdJob)
      setJobId(createdJob.id)
      setJobIdInput(createdJob.id)
      syncJobIdToUrl(createdJob.id)
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : 'Upload flow failed',
      )
    } finally {
      setUploadState('idle')
    }
  }

  const handleLoadJob = (
    event: SyntheticEvent<HTMLFormElement, SubmitEvent>,
  ) => {
    event.preventDefault()

    const normalizedJobId = jobIdInput.trim()

    if (!normalizedJobId) {
      setJobError('Enter a job id before loading a result.')
      return
    }

    setJob(null)
    setJobError(null)
    setJobId(normalizedJobId)
    syncJobIdToUrl(normalizedJobId)
  }

  return (
    <div className={styles.appShell}>
      <main className={styles.page}>
        <section className={styles.hero}>
          <span className={styles.eyebrow}>Deployment-check MVP</span>
          <h1 className={styles.title}>
            Running video upload and job tracking
          </h1>
          <p className={styles.lead}>
            This page is only for verifying the real browser flow: request a
            presigned URL, upload the source video to R2, create an analysis
            job, and poll the worker result from Render.
          </p>
        </section>

        <section className={styles.layout}>
          <article className={styles.card}>
            <h2 className={styles.cardTitle}>1. Upload a test video</h2>
            <form className={styles.form} onSubmit={handleFileUpload}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="video-file">
                  Video file
                </label>
                <input
                  className={styles.fileInput}
                  id="video-file"
                  type="file"
                  accept="video/mp4,video/quicktime,video/webm"
                  onChange={(event) => {
                    setSelectedFile(event.target.files?.[0] ?? null)
                    setFormError(null)
                  }}
                />
                <p className={styles.hint}>
                  Allowed types: MP4, MOV, and WEBM. Keep the file under 100 MB.
                </p>
              </div>

              {selectedFile ? (
                <div className={styles.fileMeta}>
                  <span>Filename: {selectedFile.name}</span>
                  <span>Content type: {selectedFile.type || 'unknown'}</span>
                  <span>Size: {formatBytes(selectedFile.size)}</span>
                </div>
              ) : null}

              {formError ? (
                <p className={`${styles.message} ${styles.errorMessage}`}>
                  {formError}
                </p>
              ) : null}

              <div className={styles.buttonRow}>
                <button
                  className={styles.button}
                  disabled={isSubmitting}
                  type="submit"
                >
                  {uploadButtonLabel}
                </button>
              </div>
            </form>
          </article>

          <article className={styles.card}>
            <h2 className={styles.cardTitle}>2. Load or reload a job result</h2>
            <form className={styles.jobIdBox} onSubmit={handleLoadJob}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="job-id">
                  Job id
                </label>
                <input
                  className={styles.textInput}
                  id="job-id"
                  type="text"
                  placeholder="Paste an existing job id"
                  value={jobIdInput}
                  onChange={(event) => {
                    setJobIdInput(event.target.value)
                    setJobError(null)
                  }}
                />
              </div>
              <div className={styles.buttonRow}>
                <button className={styles.buttonSecondary} type="submit">
                  Load job
                </button>
              </div>
            </form>
          </article>

          <article className={styles.card}>
            <h2 className={styles.cardTitle}>3. Job status</h2>
            {job ? (
              <div className={styles.statusPanel}>
                <span className={statusClassName}>{job.status}</span>
                <div className={styles.details}>
                  <div className={styles.detailCard}>
                    <span className={styles.detailLabel}>Job id</span>
                    <p className={styles.detailValue}>{job.id}</p>
                  </div>
                  <div className={styles.detailCard}>
                    <span className={styles.detailLabel}>Filename</span>
                    <p className={styles.detailValue}>
                      {job.original_filename}
                    </p>
                  </div>
                  <div className={styles.detailCard}>
                    <span className={styles.detailLabel}>Duration</span>
                    <p className={styles.detailValue}>
                      {job.video_duration_seconds ?? 'Pending'}
                    </p>
                  </div>
                  <div className={styles.detailCard}>
                    <span className={styles.detailLabel}>Resolution</span>
                    <p className={styles.detailValue}>
                      {job.video_width && job.video_height
                        ? `${job.video_width} x ${job.video_height}`
                        : 'Pending'}
                    </p>
                  </div>
                </div>

                {job.error_message ? (
                  <p className={`${styles.message} ${styles.errorMessage}`}>
                    {job.error_message}
                  </p>
                ) : null}
              </div>
            ) : (
              <p className={styles.message}>
                Upload a file or load an existing job id to start polling the
                backend status.
              </p>
            )}

            {jobError ? (
              <p className={`${styles.message} ${styles.errorMessage}`}>
                {jobError}
              </p>
            ) : null}

            <p className={styles.footerNote}>
              API base URL: <code>{API_BASE_URL}</code>
            </p>
          </article>
        </section>
      </main>
    </div>
  )
}

export default App
