import { Container, SimpleGrid, Stack, Text, Title } from '@mantine/core'

import { ClientStagesPanel } from '@/features/pipeline-check/components/ClientStagesPanel'
import { JobResultCard } from '@/features/pipeline-check/components/JobResultCard'
import { JobStatusPanel } from '@/features/pipeline-check/components/JobStatusPanel'
import { PipelineRunPanel } from '@/features/pipeline-check/components/PipelineRunPanel'
import { usePipelineCheck } from '@/features/pipeline-check/hooks/usePipelineCheck'
import { API_BASE_URL } from '@/lib/config'

export function PipelineCheckPage() {
  const pipelineCheck = usePipelineCheck()

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        <div>
          <Title order={1}>pipeline-check</Title>
          <Text c="dimmed" mt="xs">
            Run one full browser-to-worker check while keeping enough stage
            detail to locate failures.
          </Text>
          <Text size="sm" mt="sm">
            API base URL: {API_BASE_URL}
          </Text>
        </div>

        <SimpleGrid cols={{ base: 1, lg: 2 }} spacing="lg">
          <PipelineRunPanel
            selectedFile={pipelineCheck.selectedFile}
            isRunningFlow={pipelineCheck.isRunningFlow}
            flowRunError={pipelineCheck.flowRunError}
            onFileChange={pipelineCheck.onFileChange}
            onRunPipelineCheck={pipelineCheck.runPipelineCheck}
            onResetPipelineCheck={pipelineCheck.resetPipelineCheck}
          />

          <JobStatusPanel
            jobIdInput={pipelineCheck.jobIdInput}
            activeJobId={pipelineCheck.activeJobId}
            isPolling={pipelineCheck.isPolling}
            isRunningFlow={pipelineCheck.isRunningFlow}
            jobLastLoadedAt={pipelineCheck.jobLastLoadedAt}
            jobLoadError={pipelineCheck.jobLoadError}
            onJobIdInputChange={pipelineCheck.onJobIdInputChange}
            onStartPolling={pipelineCheck.startPolling}
            onStopPolling={pipelineCheck.stopPolling}
          />
        </SimpleGrid>

        <ClientStagesPanel stages={pipelineCheck.clientStages} />

        <JobResultCard job={pipelineCheck.currentJob} />
      </Stack>
    </Container>
  )
}
