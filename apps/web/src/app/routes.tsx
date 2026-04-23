import { Route, Routes } from 'react-router'

import HomePage from '@/pages/HomePage'
import UploadTestPage from '@/pages/internal/UploadTestPage'
import NotFoundPage from '@/pages/NotFoundPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/internal/upload-test" element={<UploadTestPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
