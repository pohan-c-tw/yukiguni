import { Route, Routes } from 'react-router'

import { HomePage } from '@/pages/HomePage'
import { PipelineCheckPage } from '@/pages/internal/PipelineCheckPage'
import { PoseDebugPage } from '@/pages/internal/PoseDebugPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/internal/pipeline-check" element={<PipelineCheckPage />} />
      <Route path="/internal/pose-debug/:jobId" element={<PoseDebugPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
