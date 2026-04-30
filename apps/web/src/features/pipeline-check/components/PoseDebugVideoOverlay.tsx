import type { CSSProperties } from 'react'
import { useCallback, useMemo, useRef } from 'react'

import {
  drawFrameLabel,
  drawPoseConnections,
  drawPoseLandmarks,
} from '@/features/pipeline-check/components/poseDebugOverlayDrawing'
import { useVideoFrameDrawing } from '@/features/pipeline-check/hooks/useVideoFrameDrawing'
import type {
  PoseLandmarkFrame,
  PoseLandmarksResult,
} from '@/features/pipeline-check/types'

type PoseDebugVideoOverlayProps = {
  videoUrl: string
  poseLandmarks: PoseLandmarksResult | null
}

export function PoseDebugVideoOverlay({
  videoUrl,
  poseLandmarks,
}: PoseDebugVideoOverlayProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  const frameByIndex = useMemo(() => {
    const frames = new Map<number, PoseLandmarkFrame>()

    for (const frame of poseLandmarks?.pose.frames ?? []) {
      frames.set(frame.frame_index, frame)
    }

    return frames
  }, [poseLandmarks])

  const fps = poseLandmarks?.video.fps ?? null
  const frameCount = poseLandmarks?.video.frame_count
  const videoWidth = poseLandmarks?.video.width ?? 16
  const videoHeight = poseLandmarks?.video.height ?? 9
  const videoAspectRatio = videoWidth / videoHeight

  const wrapperStyle: CSSProperties = {
    aspectRatio: `${videoWidth} / ${videoHeight}`,
    background: '#111',
    borderRadius: 8,
    marginInline: 'auto',
    overflow: 'hidden',
    position: 'relative',
    width: `min(100%, calc(50vh * ${videoAspectRatio}))`,
  }

  const drawFrame = useCallback(
    (mediaTime: number) => {
      const canvas = canvasRef.current
      const context = canvas?.getContext('2d')

      if (!canvas || !context) {
        return
      }

      const rect = canvas.getBoundingClientRect()
      const dpr = window.devicePixelRatio || 1
      const targetCanvasWidth = Math.max(1, Math.round(rect.width * dpr))
      const targetCanvasHeight = Math.max(1, Math.round(rect.height * dpr))

      if (
        canvas.width !== targetCanvasWidth ||
        canvas.height !== targetCanvasHeight
      ) {
        canvas.width = targetCanvasWidth
        canvas.height = targetCanvasHeight
      }

      context.setTransform(dpr, 0, 0, dpr, 0, 0)
      context.clearRect(0, 0, rect.width, rect.height)

      if (
        typeof fps !== 'number' ||
        fps <= 0 ||
        typeof frameCount !== 'number' ||
        frameCount <= 0
      ) {
        return
      }

      const frameIndex = Math.min(
        frameCount - 1,
        Math.max(0, Math.floor(mediaTime * fps + 1e-4)),
      )

      const frame = frameByIndex.get(frameIndex)

      if (!frame?.pose_detected) {
        drawFrameLabel(context, frameIndex, mediaTime, rect.width, false)
        return
      }

      drawPoseConnections(context, frame.landmarks, rect.width, rect.height)
      drawPoseLandmarks(context, frame.landmarks, rect.width, rect.height)
      drawFrameLabel(context, frameIndex, mediaTime, rect.width, true)
    },
    [fps, frameByIndex, frameCount],
  )

  useVideoFrameDrawing({ canvasRef, videoRef, drawFrame })

  return (
    <div style={wrapperStyle}>
      <video
        ref={videoRef}
        src={videoUrl}
        controls
        style={{
          display: 'block',
          height: '100%',
          width: '100%',
        }}
      />
      <canvas
        ref={canvasRef}
        style={{
          height: '100%',
          inset: 0,
          pointerEvents: 'none',
          position: 'absolute',
          width: '100%',
        }}
      />
    </div>
  )
}
