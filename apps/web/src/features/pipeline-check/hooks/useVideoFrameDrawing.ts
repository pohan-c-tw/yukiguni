// TODO: review
import type { RefObject } from 'react'
import { useEffect } from 'react'

type OptionalVideoFrameApi = Partial<
  Pick<
    HTMLVideoElement,
    'cancelVideoFrameCallback' | 'requestVideoFrameCallback'
  >
>

type UseVideoFrameDrawingParams = {
  canvasRef: RefObject<HTMLCanvasElement | null>
  drawFrame: (mediaTime: number) => void
  videoRef: RefObject<HTMLVideoElement | null>
}

export function useVideoFrameDrawing({
  canvasRef,
  videoRef,
  drawFrame,
}: UseVideoFrameDrawingParams) {
  useEffect(() => {
    const video = videoRef.current

    if (!video) {
      return
    }

    const videoFrameApi: OptionalVideoFrameApi = video
    let isDisposed = false
    let videoFrameHandle: number | null = null
    let animationFrameHandle: number | null = null

    const drawCurrentTime = () => {
      drawFrame(video.currentTime)
    }

    const scheduleNextVideoFrame = () => {
      if (isDisposed) {
        return
      }

      if (videoFrameApi.requestVideoFrameCallback) {
        videoFrameHandle = videoFrameApi.requestVideoFrameCallback(
          (_now, metadata) => {
            drawFrame(metadata.mediaTime)
            scheduleNextVideoFrame()
          },
        )
      }
    }

    const scheduleAnimationFrame = () => {
      if (isDisposed) {
        return
      }

      drawCurrentTime()

      if (!video.paused && !video.ended) {
        animationFrameHandle = window.requestAnimationFrame(
          scheduleAnimationFrame,
        )
      }
    }

    const handlePlay = () => {
      if (!videoFrameApi.requestVideoFrameCallback) {
        animationFrameHandle = window.requestAnimationFrame(
          scheduleAnimationFrame,
        )
      }
    }

    drawCurrentTime()

    if (videoFrameApi.requestVideoFrameCallback) {
      scheduleNextVideoFrame()
    } else {
      video.addEventListener('play', handlePlay)
    }

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
        videoFrameApi.cancelVideoFrameCallback?.(videoFrameHandle)
      }

      if (animationFrameHandle !== null) {
        window.cancelAnimationFrame(animationFrameHandle)
      }

      video.removeEventListener('play', handlePlay)
      video.removeEventListener('loadedmetadata', drawCurrentTime)
      video.removeEventListener('seeked', drawCurrentTime)
      video.removeEventListener('pause', drawCurrentTime)
      resizeObserver.disconnect()
    }
  }, [canvasRef, drawFrame, videoRef])
}
