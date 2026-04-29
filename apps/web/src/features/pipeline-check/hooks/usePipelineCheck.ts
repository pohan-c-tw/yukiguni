import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import {
  createJob,
  createPresignedUploadUrl,
  fetchJob,
  uploadFileToR2,
} from '@/features/pipeline-check/api'
import { getErrorMessage } from '@/features/pipeline-check/errors'
import { formatDateTime } from '@/features/pipeline-check/formatters'
import { isTerminalJobStatus } from '@/features/pipeline-check/status'
import type {
  AnalysisJobResponse,
  ClientStage,
  CreatePresignedUploadUrlResponse,
  StepState,
} from '@/features/pipeline-check/types'
import { POLL_INTERVAL_MS } from '@/lib/config'

type ClientStageKey = 'presign' | 'upload' | 'create-job'

type ClientStageStates = Record<ClientStageKey, StepState>

const initialClientStageStates: ClientStageStates = {
  presign: { status: 'idle', error: null },
  upload: { status: 'idle', error: null },
  'create-job': { status: 'idle', error: null },
}

export function usePipelineCheck() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isRunningFlow, setIsRunningFlow] = useState(false)
  const [flowRunError, setFlowRunError] = useState<string | null>(null)

  const [clientStageStates, setClientStageStates] = useState<ClientStageStates>(
    initialClientStageStates,
  )
  const [presignResult, setPresignResult] =
    useState<CreatePresignedUploadUrlResponse | null>(null)
  const [uploadCompletedAt, setUploadCompletedAt] = useState<string | null>(
    null,
  )
  const [createdJob, setCreatedJob] = useState<AnalysisJobResponse | null>(null)

  const clientStages = useMemo<ClientStage[]>(
    () => [
      {
        label: 'Presign URL',
        description: 'Calls the API and receives the R2 upload URL.',
        detailLabel: 'Object key',
        detailValue: presignResult?.object_key ?? null,
        state: clientStageStates.presign,
      },
      {
        label: 'Upload to R2',
        description: 'Uploads the selected video directly to object storage.',
        detailLabel: 'Uploaded at',
        detailValue: uploadCompletedAt
          ? formatDateTime(uploadCompletedAt)
          : null,
        state: clientStageStates.upload,
      },
      {
        label: 'Create job',
        description: 'Creates the analysis job and enqueues worker processing.',
        detailLabel: 'Job id',
        detailValue: createdJob?.id ?? null,
        state: clientStageStates['create-job'],
      },
    ],
    [
      clientStageStates,
      createdJob?.id,
      presignResult?.object_key,
      uploadCompletedAt,
    ],
  )

  const [jobIdInput, setJobIdInput] = useState('')
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [isPolling, setIsPolling] = useState(false)
  const [jobLastLoadedAt, setJobLastLoadedAt] = useState<string | null>(null)
  const [jobLoadError, setJobLoadError] = useState<string | null>(null)
  const [currentJob, setCurrentJob] = useState<AnalysisJobResponse | null>(null)

  const latestJobRequestId = useRef(0)

  const resetPipelineCheck = () => {
    latestJobRequestId.current += 1

    setFlowRunError(null)
    setClientStageStates(initialClientStageStates)
    setPresignResult(null)
    setUploadCompletedAt(null)
    setCreatedJob(null)

    setJobIdInput('')
    setActiveJobId(null)
    setIsPolling(false)
    setJobLastLoadedAt(null)
    setJobLoadError(null)
    setCurrentJob(null)
  }

  const handleFileChange = (file: File | null) => {
    setSelectedFile(file)
    resetPipelineCheck()
  }

  const updateClientStage = (
    key: ClientStageKey,
    status: StepState['status'],
    error: string | null = null,
  ) => {
    setClientStageStates((currentStates) => ({
      ...currentStates,
      [key]: { status, error },
    }))
  }

  const runPipelineCheck = async () => {
    const file = selectedFile

    if (!file) {
      setFlowRunError('Choose a video file before running the flow')
      return
    }

    let currentStage: ClientStageKey | null = null

    resetPipelineCheck()
    setIsRunningFlow(true)

    try {
      currentStage = 'presign'
      updateClientStage('presign', 'running')
      const nextPresignResult = await createPresignedUploadUrl({
        filename: file.name,
        content_type: file.type,
        file_size: file.size,
      })
      setPresignResult(nextPresignResult)
      updateClientStage('presign', 'success')

      currentStage = 'upload'
      updateClientStage('upload', 'running')
      await uploadFileToR2(nextPresignResult.upload_url, file)
      setUploadCompletedAt(new Date().toISOString())
      updateClientStage('upload', 'success')

      currentStage = 'create-job'
      updateClientStage('create-job', 'running')
      const nextCreatedJob = await createJob({
        original_filename: file.name,
        content_type: file.type,
        input_object_key: nextPresignResult.object_key,
      })
      setCreatedJob(nextCreatedJob)
      setJobIdInput(nextCreatedJob.id)
      setCurrentJob(nextCreatedJob)
      updateClientStage('create-job', 'success')

      currentStage = null
      await startPolling(nextCreatedJob.id)
    } catch (error) {
      const message = getErrorMessage(error, 'Flow failed unexpectedly')

      if (currentStage) {
        updateClientStage(currentStage, 'failed', message)
      }

      setFlowRunError(message)
    } finally {
      setIsRunningFlow(false)
    }
  }

  const handleJobIdInputChange = (value: string) => {
    setJobIdInput(value)
  }

  const loadJob = useCallback(
    async (jobId: string): Promise<AnalysisJobResponse | null> => {
      const normalizedJobId = jobId.trim()

      if (!normalizedJobId) {
        setJobLoadError('Enter a job id before loading job status')
        return null
      }

      latestJobRequestId.current += 1
      const requestId = latestJobRequestId.current

      try {
        const nextJob = await fetchJob(normalizedJobId)

        if (requestId !== latestJobRequestId.current) {
          return null
        }

        setJobLastLoadedAt(new Date().toISOString())
        setJobLoadError(null)
        setCurrentJob(nextJob)

        if (isTerminalJobStatus(nextJob.status)) {
          setIsPolling(false)
        }
        return nextJob
      } catch (error) {
        if (requestId !== latestJobRequestId.current) {
          return null
        }

        setIsPolling(false)
        setJobLastLoadedAt(new Date().toISOString())
        setJobLoadError(getErrorMessage(error, 'Failed to fetch job'))
        return null
      }
    },
    [],
  )

  const startPolling = async (jobId: string = jobIdInput) => {
    const normalizedJobId = jobId.trim()

    if (!normalizedJobId) {
      setJobLoadError('Enter a job id before starting polling')
      return
    }

    setActiveJobId(normalizedJobId)
    setIsPolling(true)
    setJobLastLoadedAt(null)
    setJobLoadError(null)
    setCurrentJob(null)

    await loadJob(normalizedJobId)
  }

  const stopPolling = () => {
    setIsPolling(false)
  }

  useEffect(() => {
    if (!activeJobId || !isPolling) {
      return
    }

    const timer = window.setInterval(() => {
      void loadJob(activeJobId)
    }, POLL_INTERVAL_MS)

    return () => {
      window.clearInterval(timer)
    }
  }, [activeJobId, isPolling, loadJob])

  return {
    // Flow input
    selectedFile,
    onFileChange: handleFileChange,

    // Flow state
    isRunningFlow,
    flowRunError,
    clientStages,

    // Job lookup input
    jobIdInput,
    onJobIdInputChange: handleJobIdInputChange,

    // Job polling state
    activeJobId,
    isPolling,
    jobLastLoadedAt,
    jobLoadError,

    // Job result
    currentJob,

    // Flow actions
    runPipelineCheck,
    resetPipelineCheck,

    // Polling actions
    startPolling,
    stopPolling,
  }
}
