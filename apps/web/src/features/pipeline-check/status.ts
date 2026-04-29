import type {
  AnalysisJobResponse,
  StepState,
} from '@/features/pipeline-check/types'

export function getStepBadgeColor(status: StepState['status']) {
  if (status === 'success') {
    return 'green'
  }

  if (status === 'failed') {
    return 'red'
  }

  if (status === 'running') {
    return 'blue'
  }

  return 'gray'
}

export function getJobStatusColor(status: AnalysisJobResponse['status']) {
  if (status === 'done') {
    return 'green'
  }

  if (status === 'failed') {
    return 'red'
  }

  if (status === 'processing' || status === 'validating') {
    return 'blue'
  }

  return 'gray'
}

export function isTerminalJobStatus(status: AnalysisJobResponse['status']) {
  return status === 'done' || status === 'failed'
}
