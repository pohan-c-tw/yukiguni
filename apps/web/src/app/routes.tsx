import { Route, Routes } from 'react-router'

import { HomePage } from '@/pages/HomePage'
import { PipelineCheckPage } from '@/pages/internal/PipelineCheckPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/internal/pipeline-check" element={<PipelineCheckPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
