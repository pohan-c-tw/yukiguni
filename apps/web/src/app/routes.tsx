import { Route, Routes } from 'react-router'

import { HomePage } from '@/pages/HomePage'
import { InternalAnalysisFlowPage } from '@/pages/internal/InternalAnalysisFlowPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route
        path="/internal/analysis-flow"
        element={<InternalAnalysisFlowPage />}
      />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
