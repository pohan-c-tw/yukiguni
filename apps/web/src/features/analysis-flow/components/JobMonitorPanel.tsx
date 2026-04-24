import {
  Alert,
  Button,
  Card,
  Group,
  Stack,
  Text,
  TextInput,
} from '@mantine/core'

import { JobResultCard } from '@/features/analysis-flow/components/JobResultCard'
import type { JobResponse } from '@/features/analysis-flow/types'

export type JobMonitorPanelProps = {
  jobIdInput: string
  onJobIdInputChange: (value: string) => void
  activeJobId: string | null
  isPolling: boolean
  lastUpdatedAt: string | null
  job: JobResponse | null
  jobError: string | null
  onStartPolling: () => Promise<void>
  onStopPolling: () => void
  onRefreshNow: () => Promise<void>
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return 'Not updated yet'
  }

  return new Date(value).toLocaleString()
}

export function JobMonitorPanel({
  jobIdInput,
  onJobIdInputChange,
  activeJobId,
  isPolling,
  lastUpdatedAt,
  job,
  jobError,
  onStartPolling,
  onStopPolling,
  onRefreshNow,
}: JobMonitorPanelProps) {
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="lg">
        <div>
          <Text fw={600}>Panel 2. Job monitor</Text>
          <Text size="sm" c="dimmed">
            Poll any job id and inspect its current status plus probed video
            metadata.
          </Text>
        </div>

        <TextInput
          label="Job id"
          placeholder="Paste a job id"
          value={jobIdInput}
          onChange={(event) => {
            onJobIdInputChange(event.currentTarget.value)
          }}
        />

        <Group>
          <Button
            onClick={() => {
              void onStartPolling()
            }}
          >
            {isPolling ? 'Restart polling' : 'Start polling'}
          </Button>
          <Button
            variant="light"
            onClick={() => {
              void onRefreshNow()
            }}
          >
            Refresh now
          </Button>
          <Button
            variant="default"
            disabled={!isPolling}
            onClick={onStopPolling}
          >
            Stop polling
          </Button>
        </Group>

        <Stack gap={4}>
          <Text size="sm">Active job id: {activeJobId ?? 'None'}</Text>
          <Text size="sm">Polling: {isPolling ? 'On' : 'Off'}</Text>
          <Text size="sm">Last updated: {formatDateTime(lastUpdatedAt)}</Text>
        </Stack>

        {jobError ? (
          <Alert color="red" variant="light">
            {jobError}
          </Alert>
        ) : null}

        <JobResultCard job={job} title="Job result" />
      </Stack>
    </Card>
  )
}
