import {
  Alert,
  Button,
  Card,
  Code,
  Container,
  Group,
  Loader,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router'

import { fetchAnalysisVideoUrl, fetchJob } from '@/features/pipeline-check/api'
import { getErrorMessage } from '@/features/pipeline-check/errors'
import { formatResolution } from '@/features/pipeline-check/formatters'
import type {
  AnalysisJobResponse,
  AnalysisVideoUrlResponse,
} from '@/features/pipeline-check/types'

export function PoseDebugPage() {
  const { jobId } = useParams<{ jobId: string }>()

  const [job, setJob] = useState<AnalysisJobResponse | null>(null)
  const [videoUrlResult, setVideoUrlResult] =
    useState<AnalysisVideoUrlResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)

  const loadDebugData = useCallback(async () => {
    const normalizedJobId = jobId?.trim()

    if (!normalizedJobId) {
      setLoadError('Job id is required')
      return
    }

    setIsLoading(true)
    setLoadError(null)

    try {
      const [nextJob, nextVideoUrlResult] = await Promise.all([
        fetchJob(normalizedJobId),
        fetchAnalysisVideoUrl(normalizedJobId),
      ])
      setJob(nextJob)
      setVideoUrlResult(nextVideoUrlResult)
    } catch (error) {
      setJob(null)
      setVideoUrlResult(null)
      setLoadError(getErrorMessage(error, 'Failed to load pose debug data'))
    } finally {
      setIsLoading(false)
    }
  }, [jobId])

  useEffect(() => {
    // This route page starts its initial API load after mount because the app
    // does not use React Router data loaders yet.
    // loadDebugData sets loading/error state synchronously before awaiting
    // fetches, so this intentional mount-time request needs the local lint
    // exception below.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadDebugData()
  }, [loadDebugData])

  const poseLandmarks = job?.analysis_result?.pose_landmarks ?? null

  return (
    <Container size="xl" py="xl">
      <Stack gap="lg">
        <div>
          <Title order={1}>pose-debug</Title>
          <Text c="dimmed" mt="xs">
            Inspect the normalized analysis video used by MediaPipe.
          </Text>
        </div>

        {loadError ? (
          <Alert color="red" variant="light">
            {loadError}
          </Alert>
        ) : null}

        <Card withBorder radius="md" padding="lg">
          <Stack gap="md">
            <Group justify="space-between" align="center">
              <Text fw={600}>Analysis video</Text>
              <Button
                variant="light"
                size="xs"
                loading={isLoading}
                onClick={() => void loadDebugData()}
              >
                Refresh URL
              </Button>
            </Group>

            {isLoading && !videoUrlResult ? (
              <Group gap="sm">
                <Loader size="sm" />
                <Text size="sm" c="dimmed">
                  Loading debug video...
                </Text>
              </Group>
            ) : null}

            {videoUrlResult ? (
              <video
                src={videoUrlResult.video_url}
                controls
                style={{
                  aspectRatio: '16 / 9',
                  background: '#111',
                  borderRadius: 8,
                  display: 'block',
                  maxHeight: '70vh',
                  width: '100%',
                }}
              />
            ) : null}

            {videoUrlResult ? (
              <div>
                <Text size="sm" c="dimmed">
                  Analysis video object key
                </Text>
                <Code block>{videoUrlResult.object_key}</Code>
              </div>
            ) : null}
          </Stack>
        </Card>

        <Card withBorder radius="md" padding="lg">
          <Stack gap="md">
            <Text fw={600}>Landmark data</Text>

            {poseLandmarks ? (
              <Group align="flex-start">
                <div>
                  <Text size="sm" c="dimmed">
                    Frames
                  </Text>
                  <Text>{poseLandmarks.video.frame_count}</Text>
                </div>
                <div>
                  <Text size="sm" c="dimmed">
                    Detected frames
                  </Text>
                  <Text>{poseLandmarks.pose.detected_frame_count}</Text>
                </div>
                <div>
                  <Text size="sm" c="dimmed">
                    Analysis resolution
                  </Text>
                  <Text>
                    {formatResolution(
                      poseLandmarks.video.width,
                      poseLandmarks.video.height,
                    )}
                  </Text>
                </div>
                <div>
                  <Text size="sm" c="dimmed">
                    FPS
                  </Text>
                  <Text>{poseLandmarks.video.fps ?? 'Unknown'}</Text>
                </div>
              </Group>
            ) : (
              <Text size="sm" c="dimmed">
                No pose landmarks loaded.
              </Text>
            )}
          </Stack>
        </Card>
      </Stack>
    </Container>
  )
}
