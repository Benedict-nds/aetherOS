import { apiRequest } from './client'
import { endpoints } from './endpoints'
import type { DashboardSummary } from './types'

export function getDashboardSummaryRequest() {
  return apiRequest<DashboardSummary>(endpoints.dashboard.summary)
}