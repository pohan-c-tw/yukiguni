import type { PoseLandmark } from '@/features/pipeline-check/types'

const POSE_LANDMARK_CONNECTIONS = [
  ['left_shoulder', 'right_shoulder'],
  ['left_hip', 'right_hip'],

  ['left_shoulder', 'left_hip'],
  ['right_shoulder', 'right_hip'],

  ['left_shoulder', 'left_elbow'],
  ['left_elbow', 'left_wrist'],
  ['right_shoulder', 'right_elbow'],
  ['right_elbow', 'right_wrist'],

  ['left_hip', 'left_knee'],
  ['left_knee', 'left_ankle'],
  ['right_hip', 'right_knee'],
  ['right_knee', 'right_ankle'],

  ['left_ankle', 'left_heel'],
  ['left_heel', 'left_foot_index'],
  ['right_ankle', 'right_heel'],
  ['right_heel', 'right_foot_index'],
] as const

export function drawPoseConnections(
  context: CanvasRenderingContext2D,
  landmarks: Record<string, PoseLandmark>,
  width: number,
  height: number,
) {
  context.save()

  context.lineWidth = 2
  context.lineCap = 'round'
  context.lineJoin = 'round'
  context.strokeStyle = '#36d399'

  for (const [startName, endName] of POSE_LANDMARK_CONNECTIONS) {
    const start = landmarks[startName]
    const end = landmarks[endName]

    if (!start || !end) {
      continue
    }

    context.globalAlpha =
      Math.max(0.25, Math.min(start.visibility, end.visibility)) * 0.85
    context.beginPath()
    context.moveTo(start.x * width, start.y * height)
    context.lineTo(end.x * width, end.y * height)
    context.stroke()
  }

  context.restore()
}

export function drawPoseLandmarks(
  context: CanvasRenderingContext2D,
  landmarks: Record<string, PoseLandmark>,
  width: number,
  height: number,
) {
  context.save()

  context.lineWidth = 1.25
  context.fillStyle = '#f8fafc'
  context.strokeStyle = '#111827'

  for (const landmark of Object.values(landmarks)) {
    const x = landmark.x * width
    const y = landmark.y * height
    const radius = landmark.visibility >= 0.5 ? 3.5 : 2.5

    context.globalAlpha = Math.max(0.25, landmark.visibility)
    context.beginPath()
    context.arc(x, y, radius, 0, Math.PI * 2)
    context.fill()
    context.stroke()
  }

  context.restore()
}

export function drawFrameLabel(
  context: CanvasRenderingContext2D,
  frameIndex: number,
  mediaTime: number,
  width: number,
  poseDetected: boolean,
) {
  const label = `frame ${frameIndex} | ${mediaTime.toFixed(3)}s | ${
    poseDetected ? 'pose detected' : 'no pose'
  }`
  const paddingX = 8
  const paddingY = 5
  const originX = 8
  const originY = 8
  const labelHeight = 24

  context.save()

  context.font = '12px system-ui, -apple-system, BlinkMacSystemFont, sans-serif'
  context.textBaseline = 'top'

  const textWidth = context.measureText(label).width
  const boxWidth = Math.min(width - originX * 2, textWidth + paddingX * 2)

  context.fillStyle = 'rgba(17, 24, 39, 0.76)'
  context.fillRect(originX, originY, boxWidth, labelHeight)

  context.fillStyle = '#f8fafc'
  context.fillText(
    label,
    originX + paddingX,
    originY + paddingY,
    boxWidth - paddingX * 2,
  )

  context.restore()
}
