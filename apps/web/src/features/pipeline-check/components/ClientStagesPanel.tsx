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

import { getStepBadgeColor } from '@/features/pipeline-check/status'
import type { ClientStage } from '@/features/pipeline-check/types'

export type ClientStagesPanelProps = {
  stages: ClientStage[]
}

export function ClientStagesPanel({ stages }: ClientStagesPanelProps) {
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="lg">
        <div>
          <Text fw={600}>Client stages</Text>
          <Text size="sm" c="dimmed">
            These stages locate failures before the worker receives the job.
          </Text>
        </div>

        <SimpleGrid cols={{ base: 1, md: 3 }} spacing="md">
          {stages.map((stage) => (
            <Card key={stage.label} withBorder radius="md" padding="md">
              <Stack gap="sm">
                <Group justify="space-between" align="flex-start">
                  <div>
                    <Text fw={600}>{stage.label}</Text>
                    <Text size="sm" c="dimmed">
                      {stage.description}
                    </Text>
                  </div>
                  <Badge
                    color={getStepBadgeColor(stage.state.status)}
                    variant="light"
                  >
                    {stage.state.status}
                  </Badge>
                </Group>

                {stage.detailValue ? (
                  <Text size="sm">
                    {stage.detailLabel}:{' '}
                    <Code style={{ overflowWrap: 'anywhere' }}>
                      {stage.detailValue}
                    </Code>
                  </Text>
                ) : null}

                {stage.state.error ? (
                  <Alert color="red" variant="light">
                    {stage.state.error}
                  </Alert>
                ) : null}
              </Stack>
            </Card>
          ))}
        </SimpleGrid>
      </Stack>
    </Card>
  )
}
