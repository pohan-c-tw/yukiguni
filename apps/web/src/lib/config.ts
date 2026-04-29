const rawApiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.trim() || 'http://127.0.0.1:8000'

export const API_BASE_URL = rawApiBaseUrl.replace(/\/+$/, '')

export const POLL_INTERVAL_MS = 3000
