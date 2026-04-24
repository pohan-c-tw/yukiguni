import {
  Alert,
  Badge,
  Card,
  Code,
  Group,
  SimpleGrid,
  Stack,
  Text,
} from '@mantine/core'

import type { JobResponse } from '@/features/analysis-flow/types'

export type JobResultCardProps = {
  job: JobResponse | null
  title: string
}

function getStatusColor(status: JobResponse['status']) {
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

function formatDateTime(value: string | null): string {
  if (!value) {
    return 'Pending'
  }

  return new Date(value).toLocaleString()
}

function formatResolution(job: JobResponse): string {
  if (!job.video_width || !job.video_height) {
    return 'Pending'
  }

  return `${job.video_width} x ${job.video_height}`
}

export function JobResultCard({ job, title }: JobResultCardProps) {
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="md">
        <Text fw={600}>{title}</Text>

        {job ? (
          <>
            <Group justify="space-between" align="center">
              <Text size="sm" c="dimmed">
                Current job status
              </Text>
              <Badge color={getStatusColor(job.status)} variant="light">
                {job.status}
              </Badge>
            </Group>

            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
              <div>
                <Text size="sm" c="dimmed">
                  Job id
                </Text>
                <Code block>{job.id}</Code>
              </div>

              <div>
                <Text size="sm" c="dimmed">
                  Filename
                </Text>
                <Text>{job.original_filename}</Text>
              </div>

              <div>
                <Text size="sm" c="dimmed">
                  Duration
                </Text>
                <Text>{job.video_duration_seconds ?? 'Pending'}</Text>
              </div>

              <div>
                <Text size="sm" c="dimmed">
                  Resolution
                </Text>
                <Text>{formatResolution(job)}</Text>
              </div>

              <div>
                <Text size="sm" c="dimmed">
                  Processing started
                </Text>
                <Text>{formatDateTime(job.processing_started_at)}</Text>
              </div>

              <div>
                <Text size="sm" c="dimmed">
                  Completed
                </Text>
                <Text>{formatDateTime(job.completed_at)}</Text>
              </div>

              <div>
                <Text size="sm" c="dimmed">
                  Failed
                </Text>
                <Text>{formatDateTime(job.failed_at)}</Text>
              </div>

              <div>
                <Text size="sm" c="dimmed">
                  Object key
                </Text>
                <Code block>{job.input_object_key}</Code>
              </div>
            </SimpleGrid>

            {job.error_message ? (
              <Alert color="red" variant="light">
                {job.error_message}
              </Alert>
            ) : null}
          </>
        ) : (
          <Text size="sm" c="dimmed">
            No job loaded yet.
          </Text>
        )}
      </Stack>
    </Card>
  )
}
