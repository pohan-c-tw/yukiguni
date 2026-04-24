import { Container, Grid, Stack, Text, Title } from '@mantine/core'
import { useEffect } from 'react'

import { FlowActionPanel } from '@/features/analysis-flow/components/FlowActionPanel'
import { JobMonitorPanel } from '@/features/analysis-flow/components/JobMonitorPanel'
import { useAnalysisFlowActions } from '@/features/analysis-flow/hooks/useAnalysisFlowActions'
import { useJobMonitor } from '@/features/analysis-flow/hooks/useJobMonitor'
import { API_BASE_URL } from '@/lib/config'

export function InternalAnalysisFlowPage() {
  const flow = useAnalysisFlowActions()

  const monitor = useJobMonitor()
  const { loadJobFromFlow } = monitor

  useEffect(() => {
    if (!flow.createdJob?.id) {
      return
    }

    void loadJobFromFlow(flow.createdJob.id)
  }, [flow.createdJob?.id, loadJobFromFlow])

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        <div>
          <Title order={1}>Internal analysis flow</Title>
          <Text c="dimmed" mt="xs">
            Verify the deployment-check MVP by testing presign URL creation,
            direct upload to R2, job creation, and job status polling.
          </Text>
          <Text size="sm" mt="sm">
            API base URL: {API_BASE_URL}
          </Text>
        </div>

        <Grid gap="lg" align="start">
          <Grid.Col span={{ base: 12, lg: 7 }}>
            <FlowActionPanel
              selectedFile={flow.selectedFile}
              onFileChange={flow.setSelectedFile}
              stepStates={flow.stepStates}
              isBusy={flow.isBusy}
              presignResult={flow.presignResult}
              uploadCompletedAt={flow.uploadCompletedAt}
              createdJob={flow.createdJob}
              runAllError={flow.runAllError}
              onRequestPresignUrl={flow.requestPresignUrl}
              onUploadToR2={flow.uploadToPresignedUrl}
              onCreateJob={flow.createAnalysisJob}
              onRunAll={flow.runAll}
            />
          </Grid.Col>

          <Grid.Col span={{ base: 12, lg: 5 }}>
            <JobMonitorPanel
              jobIdInput={monitor.jobIdInput}
              onJobIdInputChange={monitor.setJobIdInput}
              activeJobId={monitor.activeJobId}
              isPolling={monitor.isPolling}
              lastUpdatedAt={monitor.lastUpdatedAt}
              job={monitor.job}
              jobError={monitor.jobError}
              onStartPolling={() => monitor.startPolling()}
              onStopPolling={() => monitor.stopPolling()}
              onRefreshNow={() => monitor.refreshJob()}
            />
          </Grid.Col>
        </Grid>
      </Stack>
    </Container>
  )
}
