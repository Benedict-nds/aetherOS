import { apiRequest } from './client'
import { endpoints } from './endpoints'
import type { ExpiryRow, LowStockRow } from './types'

export function getLowStockReportRequest() {
  return apiRequest<LowStockRow[]>(endpoints.reports.lowStock)
}

export function getExpiryReportRequest(withinDays: number) {
  return apiRequest<ExpiryRow[]>(endpoints.reports.expiry, {
    params: { within_days: withinDays },
  })
}
