import type { RefObject } from 'react'
import { useEffect } from 'react'

type UseVideoFrameDrawingParams = {
  canvasRef: RefObject<HTMLCanvasElement | null>
  videoRef: RefObject<HTMLVideoElement | null>
  drawFrame: (mediaTime: number) => void
}

export function useVideoFrameDrawing({
  canvasRef,
  videoRef,
  drawFrame,
}: UseVideoFrameDrawingParams) {
  useEffect(() => {
    const video = videoRef.current

    if (!video || !video.requestVideoFrameCallback) {
      return
    }

    let isDisposed = false
    let videoFrameHandle: number | null = null

    const drawCurrentTime = () => {
      drawFrame(video.currentTime)
    }

    const scheduleNextVideoFrame = () => {
      if (isDisposed) {
        return
      }

      videoFrameHandle = video.requestVideoFrameCallback((_now, metadata) => {
        drawFrame(metadata.mediaTime)
        scheduleNextVideoFrame()
      })
    }

    drawCurrentTime()
    scheduleNextVideoFrame()

    video.addEventListener('loadedmetadata', drawCurrentTime)
    video.addEventListener('seeked', drawCurrentTime)
    video.addEventListener('pause', drawCurrentTime)

    const resizeObserver = new ResizeObserver(drawCurrentTime)

    if (canvasRef.current) {
      resizeObserver.observe(canvasRef.current)
    }

    return () => {
      isDisposed = true

      if (videoFrameHandle !== null) {
        video.cancelVideoFrameCallback(videoFrameHandle)
      }

      video.removeEventListener('loadedmetadata', drawCurrentTime)
      video.removeEventListener('seeked', drawCurrentTime)
      video.removeEventListener('pause', drawCurrentTime)
      resizeObserver.disconnect()
    }
  }, [canvasRef, drawFrame, videoRef])
}
