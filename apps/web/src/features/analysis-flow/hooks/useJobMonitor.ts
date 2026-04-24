import { useCallback, useEffect, useRef, useState } from 'react'

import { fetchJob } from '@/features/analysis-flow/api'
import type { JobResponse } from '@/features/analysis-flow/types'
import { POLL_INTERVAL_MS } from '@/lib/config'

function isTerminalStatus(status: JobResponse['status']) {
  return status === 'done' || status === 'failed'
}

export function useJobMonitor() {
  const [jobIdInput, setJobIdInput] = useState('')
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [isPolling, setIsPolling] = useState(false)
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null)
  const latestRequestId = useRef(0)

  const [job, setJob] = useState<JobResponse | null>(null)
  const [jobError, setJobError] = useState<string | null>(null)

  const refreshJob = useCallback(
    async (jobIdOverride?: string) => {
      const jobId = (jobIdOverride ?? activeJobId ?? jobIdInput).trim()

      if (!jobId) {
        setJobError('Enter a job id before loading job status.')
        return
      }

      latestRequestId.current += 1
      const requestId = latestRequestId.current

      try {
        const nextJob = await fetchJob(jobId)

        if (requestId !== latestRequestId.current) {
          return
        }

        setJob(nextJob)
        setJobError(null)
        setLastUpdatedAt(new Date().toISOString())

        if (isTerminalStatus(nextJob.status)) {
          setIsPolling(false)
        }
      } catch (error) {
        if (requestId !== latestRequestId.current) {
          return
        }

        setJobError(
          error instanceof Error ? error.message : 'Failed to fetch job',
        )
        setLastUpdatedAt(new Date().toISOString())
        setIsPolling(false)
      }
    },
    [activeJobId, jobIdInput],
  )

  const startPolling = useCallback(
    async (jobIdOverride?: string) => {
      const normalizedJobId = (jobIdOverride ?? jobIdInput).trim()

      if (!normalizedJobId) {
        setJobError('Enter a job id before starting polling.')
        return
      }

      setJobIdInput(normalizedJobId)
      setActiveJobId(normalizedJobId)
      setIsPolling(true)
      setLastUpdatedAt(null)

      await refreshJob(normalizedJobId)
    },
    [jobIdInput, refreshJob],
  )

  const stopPolling = useCallback(() => {
    setIsPolling(false)
  }, [])

  const loadJobFromFlow = useCallback(
    async (jobId: string) => {
      setJobIdInput(jobId)
      await startPolling(jobId)
    },
    [startPolling],
  )

  useEffect(() => {
    if (!activeJobId || !isPolling) {
      return
    }

    const timer = window.setInterval(() => {
      void refreshJob(activeJobId)
    }, POLL_INTERVAL_MS)

    return () => {
      window.clearInterval(timer)
    }
  }, [activeJobId, isPolling, refreshJob])

  return {
    jobIdInput,
    setJobIdInput,
    activeJobId,
    isPolling,
    lastUpdatedAt,
    job,
    jobError,
    startPolling,
    stopPolling,
    refreshJob,
    loadJobFromFlow,
  }
}
