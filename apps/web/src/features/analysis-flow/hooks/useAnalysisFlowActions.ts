import { useMemo, useState } from 'react'

import {
  createJob,
  createUploadUrl,
  uploadFileToR2,
} from '@/features/analysis-flow/api'
import type {
  CreateJobRequest,
  JobResponse,
  StepKey,
  StepStates,
  UploadUrlResponse,
} from '@/features/analysis-flow/types'

const initialStepStates: StepStates = {
  presign: { status: 'idle', error: null },
  upload: { status: 'idle', error: null },
  'create-job': { status: 'idle', error: null },
}

function createNextStepStates(
  previousState: StepStates,
  key: StepKey,
  status: StepStates[StepKey]['status'],
  error: string | null,
): StepStates {
  return {
    ...previousState,
    [key]: {
      status,
      error,
    },
  }
}

export function useAnalysisFlowActions() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [stepStates, setStepStates] = useState<StepStates>(initialStepStates)
  const [presignResult, setPresignResult] = useState<UploadUrlResponse | null>(
    null,
  )
  const [uploadCompletedAt, setUploadCompletedAt] = useState<string | null>(
    null,
  )
  const [createdJob, setCreatedJob] = useState<JobResponse | null>(null)
  const [runAllError, setRunAllError] = useState<string | null>(null)

  const isBusy = useMemo(
    () =>
      Object.values(stepStates).some(
        (stepState) => stepState.status === 'running',
      ),
    [stepStates],
  )

  const handleFileChange = (file: File | null) => {
    setSelectedFile(file)
    setStepStates(initialStepStates)
    setPresignResult(null)
    setUploadCompletedAt(null)
    setCreatedJob(null)
    setRunAllError(null)
  }

  const clearResultsFromStep = (step: StepKey) => {
    setRunAllError(null)

    if (step === 'presign') {
      setStepStates((currentState) => ({
        presign: currentState.presign,
        upload: { status: 'idle', error: null },
        'create-job': { status: 'idle', error: null },
      }))
      setPresignResult(null)
      setUploadCompletedAt(null)
      setCreatedJob(null)
      return
    }

    if (step === 'upload') {
      setStepStates((currentState) => ({
        ...currentState,
        'create-job': { status: 'idle', error: null },
      }))
      setUploadCompletedAt(null)
      setCreatedJob(null)
    }
  }

  const runStep = async <T>(
    key: StepKey,
    callback: () => Promise<T>,
  ): Promise<T> => {
    setRunAllError(null)

    setStepStates((currentState) =>
      createNextStepStates(currentState, key, 'running', null),
    )

    try {
      const result = await callback()
      setStepStates((currentState) =>
        createNextStepStates(currentState, key, 'success', null),
      )
      return result
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unexpected step failure'
      setStepStates((currentState) =>
        createNextStepStates(currentState, key, 'failed', message),
      )
      throw new Error(message)
    }
  }

  const requestPresignUrl = async (): Promise<UploadUrlResponse> => {
    return runStep('presign', async () => {
      if (!selectedFile) {
        throw new Error(
          'Choose a video file before requesting a presigned URL.',
        )
      }

      clearResultsFromStep('presign')

      const response = await createUploadUrl({
        filename: selectedFile.name,
        content_type: selectedFile.type,
        file_size: selectedFile.size,
      })
      setPresignResult(response)
      return response
    })
  }

  const uploadToPresignedUrl = async (): Promise<void> => {
    await runStep('upload', async () => {
      if (!selectedFile) {
        throw new Error('Choose a video file before uploading.')
      }

      if (!presignResult) {
        throw new Error('Request a presigned URL before uploading to R2.')
      }

      clearResultsFromStep('upload')

      await uploadFileToR2(presignResult.upload_url, selectedFile)
      setUploadCompletedAt(new Date().toISOString())
    })
  }

  const createAnalysisJob = async (): Promise<JobResponse> => {
    return runStep('create-job', async () => {
      if (!selectedFile) {
        throw new Error('Choose a video file before creating a job.')
      }

      if (!presignResult) {
        throw new Error('Request a presigned URL before creating a job.')
      }

      if (!uploadCompletedAt) {
        throw new Error('Upload the file to R2 before creating a job.')
      }

      const payload: CreateJobRequest = {
        original_filename: selectedFile.name,
        content_type: selectedFile.type,
        input_object_key: presignResult.object_key,
      }
      const job = await createJob(payload)
      setCreatedJob(job)
      return job
    })
  }

  const runAll = async (): Promise<JobResponse> => {
    try {
      if (!selectedFile) {
        throw new Error('Choose a video file before running the full flow.')
      }

      const nextPresignResult = await requestPresignUrl()

      if (!nextPresignResult) {
        throw new Error('Failed to request a presigned URL.')
      }

      await runStep('upload', async () => {
        await uploadFileToR2(nextPresignResult.upload_url, selectedFile)
        setUploadCompletedAt(new Date().toISOString())
      })

      return await runStep('create-job', async () => {
        const payload: CreateJobRequest = {
          original_filename: selectedFile.name,
          content_type: selectedFile.type,
          input_object_key: nextPresignResult.object_key,
        }
        const job = await createJob(payload)
        setCreatedJob(job)
        return job
      })
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Run all failed unexpectedly'
      setRunAllError(message)
      throw error
    }
  }

  return {
    selectedFile,
    setSelectedFile: handleFileChange,
    stepStates,
    isBusy,
    presignResult,
    uploadCompletedAt,
    createdJob,
    runAllError,
    requestPresignUrl,
    uploadToPresignedUrl,
    createAnalysisJob,
    runAll,
  }
}
