import { Alert, Badge, Card, Code, Group, Stack, Text } from '@mantine/core'

import type { StepState } from '@/features/analysis-flow/types'

export type StepStatusCardProps = {
  title: string
  description: string
  state: StepState
  detailLabel?: string
  detailValue?: string | null
  action: React.ReactNode
}

function getBadgeColor(status: StepState['status']) {
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

export function StepStatusCard({
  title,
  description,
  state,
  detailLabel,
  detailValue,
  action,
}: StepStatusCardProps) {
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="md">
        <Group justify="space-between" align="flex-start">
          <div>
            <Text fw={600}>{title}</Text>
            <Text size="sm" c="dimmed">
              {description}
            </Text>
          </div>
          <Badge color={getBadgeColor(state.status)} variant="light">
            {state.status}
          </Badge>
        </Group>

        {detailLabel && detailValue ? (
          <Text size="sm">
            {detailLabel}:{' '}
            <Code
              style={{
                overflowWrap: 'anywhere',
              }}
            >
              {detailValue}
            </Code>
          </Text>
        ) : null}

        {state.error ? (
          <Alert color="red" variant="light">
            {state.error}
          </Alert>
        ) : null}

        {action}
      </Stack>
    </Card>
  )
}
