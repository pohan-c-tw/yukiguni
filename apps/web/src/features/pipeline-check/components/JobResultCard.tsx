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

import {
  formatDateTime,
  formatResolution,
} from '@/features/pipeline-check/formatters'
import { getJobStatusColor } from '@/features/pipeline-check/status'
import type { AnalysisJobResponse } from '@/features/pipeline-check/types'

export type JobResultCardProps = {
  job: AnalysisJobResponse | null
}

export function JobResultCard({ job }: JobResultCardProps) {
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="md">
        <Text fw={600}>Worker result</Text>

        {job ? (
          <>
            <Group justify="space-between" align="center">
              <Text size="sm" c="dimmed">
                Current job status
              </Text>
              <Badge color={getJobStatusColor(job.status)} variant="light">
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

            {job.analysis_result ? (
              <div>
                <Text size="sm" c="dimmed">
                  Analysis result
                </Text>
                <Code block>
                  {JSON.stringify(job.analysis_result, null, 2)}
                </Code>
              </div>
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
