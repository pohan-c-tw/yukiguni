import {
  Alert,
  Button,
  Card,
  Code,
  Group,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
} from '@mantine/core'

import { formatDateTime } from '@/features/pipeline-check/formatters'

export type JobStatusPanelProps = {
  jobIdInput: string
  activeJobId: string | null
  isPolling: boolean
  isRunningFlow: boolean
  jobLastLoadedAt: string | null
  jobLoadError: string | null
  onJobIdInputChange: (value: string) => void
  onStartPolling: () => Promise<void>
  onStopPolling: () => void
}

export function JobStatusPanel({
  jobIdInput,
  activeJobId,
  isPolling,
  isRunningFlow,
  jobLastLoadedAt,
  jobLoadError,
  onJobIdInputChange,
  onStartPolling,
  onStopPolling,
}: JobStatusPanelProps) {
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="lg">
        <div>
          <Text fw={600}>Job status</Text>
          <Text size="sm" c="dimmed">
            The created job starts polling automatically. You can also inspect
            an existing job id.
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
            disabled={isRunningFlow}
            onClick={() => {
              void onStartPolling()
            }}
          >
            Start polling
          </Button>
          <Button
            variant="default"
            disabled={isRunningFlow || !isPolling}
            onClick={() => {
              onStopPolling()
            }}
          >
            Stop polling
          </Button>
        </Group>

        <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="sm">
          <div>
            <Text size="sm" c="dimmed">
              Active job id
            </Text>
            <Code block>{activeJobId ?? 'None'}</Code>
          </div>
          <div>
            <Text size="sm" c="dimmed">
              Polling
            </Text>
            <Text size="sm">{isPolling ? 'On' : 'Off'}</Text>
          </div>
          <div>
            <Text size="sm" c="dimmed">
              Last loaded
            </Text>
            <Text size="sm">{formatDateTime(jobLastLoadedAt)}</Text>
          </div>
        </SimpleGrid>

        {jobLoadError ? (
          <Alert color="red" variant="light">
            {jobLoadError}
          </Alert>
        ) : null}
      </Stack>
    </Card>
  )
}
