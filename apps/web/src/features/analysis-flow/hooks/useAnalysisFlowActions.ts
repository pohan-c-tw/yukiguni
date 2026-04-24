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

type FlowResultKey = 'presignResult' | 'uploadCompletedAt' | 'createdJob'

type FlowStepDefinition = {
  stepsToReset: StepKey[]
  resultsToClear: FlowResultKey[]
}

const initialStepStates: StepStates = {
  presign: { status: 'idle', error: null },
  upload: { status: 'idle', error: null },
  'create-job': { status: 'idle', error: null },
}

const flowStepDefinitions: Record<StepKey, FlowStepDefinition> = {
  presign: {
    stepsToReset: ['upload', 'create-job'],
    resultsToClear: ['presignResult', 'uploadCompletedAt', 'createdJob'],
  },
  upload: {
    stepsToReset: ['create-job'],
    resultsToClear: ['uploadCompletedAt', 'createdJob'],
  },
  'create-job': {
    stepsToReset: [],
    resultsToClear: ['createdJob'],
  },
}

function resetStepStates(
  currentState: StepStates,
  stepsToReset: StepKey[],
): StepStates {
  return stepsToReset.reduce(
    (nextState, step) => ({
      ...nextState,
      [step]: { status: 'idle', error: null },
    }),
    currentState,
  )
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

  const clearFlowResultsForFileChange = () => {
    setStepStates(initialStepStates)
    setPresignResult(null)
    setUploadCompletedAt(null)
    setCreatedJob(null)
    setRunAllError(null)
  }

  const handleFileChange = (file: File | null) => {
    setSelectedFile(file)
    clearFlowResultsForFileChange()
  }

  const clearResultsFromStep = (step: StepKey) => {
    const definition = flowStepDefinitions[step]

    setStepStates((currentState) =>
      resetStepStates(currentState, definition.stepsToReset),
    )

    if (definition.resultsToClear.includes('presignResult')) {
      setPresignResult(null)
    }

    if (definition.resultsToClear.includes('uploadCompletedAt')) {
      setUploadCompletedAt(null)
    }

    if (definition.resultsToClear.includes('createdJob')) {
      setCreatedJob(null)
    }

    setRunAllError(null)
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
    clearResultsFromStep('presign')

    return runStep('presign', async () => {
      const file = selectedFile

      if (!file) {
        throw new Error(
          'Choose a video file before requesting a presigned URL.',
        )
      }

      const response = await createUploadUrl({
        filename: file.name,
        content_type: file.type,
        file_size: file.size,
      })
      setPresignResult(response)
      return response
    })
  }

  const uploadToPresignedUrl = async (
    nextPresignResult = presignResult,
  ): Promise<void> => {
    clearResultsFromStep('upload')

    await runStep('upload', async () => {
      const file = selectedFile

      if (!file) {
        throw new Error('Choose a video file before uploading.')
      }

      if (!nextPresignResult) {
        throw new Error('Request a presigned URL before uploading to R2.')
      }

      await uploadFileToR2(nextPresignResult.upload_url, file)
      setUploadCompletedAt(new Date().toISOString())
    })
  }

  const createAnalysisJob = async (
    nextPresignResult = presignResult,
    hasUploaded = Boolean(uploadCompletedAt),
  ): Promise<JobResponse> => {
    clearResultsFromStep('create-job')

    return runStep('create-job', async () => {
      const file = selectedFile

      if (!file) {
        throw new Error('Choose a video file before creating a job.')
      }

      if (!nextPresignResult) {
        throw new Error('Request a presigned URL before creating a job.')
      }

      if (!hasUploaded) {
        throw new Error('Upload the file to R2 before creating a job.')
      }

      const payload: CreateJobRequest = {
        original_filename: file.name,
        content_type: file.type,
        input_object_key: nextPresignResult.object_key,
      }
      const job = await createJob(payload)
      setCreatedJob(job)
      return job
    })
  }

  const runAll = async (): Promise<JobResponse> => {
    try {
      const nextPresignResult = await requestPresignUrl()

      await uploadToPresignedUrl(nextPresignResult)

      return await createAnalysisJob(nextPresignResult, true)
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
