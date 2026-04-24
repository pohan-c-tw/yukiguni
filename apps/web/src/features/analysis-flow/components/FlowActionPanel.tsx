import {
  Alert,
  Button,
  Card,
  Code,
  FileInput,
  Group,
  Stack,
  Text,
} from '@mantine/core'

import { StepStatusCard } from '@/features/analysis-flow/components/StepStatusCard'
import type {
  JobResponse,
  StepStates,
  UploadUrlResponse,
} from '@/features/analysis-flow/types'

export type FlowActionPanelProps = {
  selectedFile: File | null
  onFileChange: (file: File | null) => void
  stepStates: StepStates
  isBusy: boolean
  presignResult: UploadUrlResponse | null
  uploadCompletedAt: string | null
  createdJob: JobResponse | null
  runAllError: string | null
  onRequestPresignUrl: () => Promise<unknown>
  onUploadToR2: () => Promise<void>
  onCreateJob: () => Promise<unknown>
  onRunAll: () => Promise<unknown>
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return 'Pending'
  }

  return new Date(value).toLocaleString()
}

export function FlowActionPanel({
  selectedFile,
  onFileChange,
  stepStates,
  isBusy,
  presignResult,
  uploadCompletedAt,
  createdJob,
  runAllError,
  onRequestPresignUrl,
  onUploadToR2,
  onCreateJob,
  onRunAll,
}: FlowActionPanelProps) {
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="lg">
        <div>
          <Text fw={600}>Panel 1. Flow actions</Text>
          <Text size="sm" c="dimmed">
            Test each client step independently or run the full presign to job
            flow in one action.
          </Text>
        </div>

        <Card withBorder radius="md" padding="lg">
          <Stack gap="md">
            <div>
              <Text fw={600}>Step 1. Select file</Text>
              <Text size="sm" c="dimmed">
                Choose one video file before requesting a presigned upload URL.
              </Text>
            </div>

            <FileInput
              accept="video/mp4,video/quicktime,video/webm"
              clearable
              disabled={isBusy}
              label="Video file"
              placeholder="Select a video"
              value={selectedFile}
              onChange={onFileChange}
            />

            {selectedFile ? (
              <Stack gap={4}>
                <Text size="sm">Filename: {selectedFile.name}</Text>
                <Text size="sm">
                  Content type: {selectedFile.type || 'unknown'}
                </Text>
                <Text size="sm">Size: {formatBytes(selectedFile.size)}</Text>
              </Stack>
            ) : (
              <Text size="sm" c="dimmed">
                Allowed types: MP4, MOV, WEBM. File size limit is 100 MB.
              </Text>
            )}
          </Stack>
        </Card>

        <StepStatusCard
          title="Step 2. Request presigned URL"
          description="Calls the API and stores the upload URL plus object key."
          state={stepStates.presign}
          detailLabel="Object key"
          detailValue={presignResult?.object_key ?? null}
          action={
            <Button
              variant="light"
              disabled={isBusy}
              loading={stepStates.presign.status === 'running'}
              onClick={() => {
                void onRequestPresignUrl()
              }}
            >
              Request presigned URL
            </Button>
          }
        />

        <StepStatusCard
          title="Step 3. Upload to presigned URL"
          description="Uploads the selected file directly to Cloudflare R2."
          state={stepStates.upload}
          detailLabel="Uploaded at"
          detailValue={
            uploadCompletedAt ? formatDateTime(uploadCompletedAt) : null
          }
          action={
            <Button
              variant="light"
              disabled={isBusy}
              loading={stepStates.upload.status === 'running'}
              onClick={() => {
                void onUploadToR2()
              }}
            >
              Upload to R2
            </Button>
          }
        />

        <StepStatusCard
          title="Step 4. Create analysis job"
          description="Creates an analysis job after the upload is in R2."
          state={stepStates['create-job']}
          detailLabel="Created job id"
          detailValue={createdJob?.id ?? null}
          action={
            <Button
              variant="light"
              disabled={isBusy}
              loading={stepStates['create-job'].status === 'running'}
              onClick={() => {
                void onCreateJob()
              }}
            >
              Create job
            </Button>
          }
        />

        <Group justify="space-between" align="center">
          <Text size="sm" c="dimmed">
            Run all executes step 2 to step 4 in order.
          </Text>
          <Button
            disabled={isBusy}
            loading={isBusy}
            onClick={() => {
              void onRunAll()
            }}
          >
            Run all
          </Button>
        </Group>

        {runAllError ? (
          <Alert color="red" variant="light">
            {runAllError}
          </Alert>
        ) : null}

        {presignResult ? (
          <Text size="sm">
            Presign expires in {presignResult.expires_in_seconds} seconds.
            Upload URL is stored in memory only for this page session.
          </Text>
        ) : null}

        {createdJob ? (
          <Alert color="green" variant="light">
            Job created successfully: <Code>{createdJob.id}</Code>
          </Alert>
        ) : null}
      </Stack>
    </Card>
  )
}
