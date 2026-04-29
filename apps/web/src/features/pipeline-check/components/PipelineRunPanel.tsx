import {
  Alert,
  Button,
  Card,
  FileInput,
  Group,
  SimpleGrid,
  Stack,
  Text,
} from '@mantine/core'

import { formatBytes } from '@/features/pipeline-check/formatters'

export type PipelineRunPanelProps = {
  selectedFile: File | null
  isRunningFlow: boolean
  flowRunError: string | null
  onFileChange: (file: File | null) => void
  onRunPipelineCheck: () => Promise<void>
  onResetPipelineCheck: () => void
}

export function PipelineRunPanel({
  selectedFile,
  isRunningFlow,
  flowRunError,
  onFileChange,
  onRunPipelineCheck,
  onResetPipelineCheck,
}: PipelineRunPanelProps) {
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="lg">
        <div>
          <Text fw={600}>Smoke test</Text>
          <Text size="sm" c="dimmed">
            Select one video and run presign, upload, job creation, and polling
            in order.
          </Text>
        </div>

        <FileInput
          label="Video file"
          placeholder="Select a video"
          value={selectedFile}
          disabled={isRunningFlow}
          accept="video/mp4,video/quicktime,video/webm"
          clearable
          onChange={onFileChange}
        />

        {selectedFile ? (
          <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="sm">
            <div>
              <Text size="sm" c="dimmed">
                Filename
              </Text>
              <Text size="sm">{selectedFile.name}</Text>
            </div>
            <div>
              <Text size="sm" c="dimmed">
                Content type
              </Text>
              <Text size="sm">{selectedFile.type || 'unknown'}</Text>
            </div>
            <div>
              <Text size="sm" c="dimmed">
                Size
              </Text>
              <Text size="sm">{formatBytes(selectedFile.size)}</Text>
            </div>
          </SimpleGrid>
        ) : (
          <Text size="sm" c="dimmed">
            Allowed types: MP4, MOV, WEBM. File size limit is 100 MB.
          </Text>
        )}

        <Group>
          <Button
            disabled={!selectedFile || isRunningFlow}
            loading={isRunningFlow}
            onClick={() => {
              void onRunPipelineCheck()
            }}
          >
            Run pipeline check
          </Button>
          <Button
            variant="default"
            disabled={isRunningFlow}
            onClick={() => {
              onResetPipelineCheck()
            }}
          >
            Clear status
          </Button>
        </Group>

        {flowRunError ? (
          <Alert color="red" variant="light">
            {flowRunError}
          </Alert>
        ) : null}
      </Stack>
    </Card>
  )
}
