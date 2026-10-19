import { apiRequest } from './client'
import { endpoints } from './endpoints'
import type { Medicine, MedicineBatch, MedicineCategory } from './types'

export function listMedicinesRequest(params?: { q?: string; category_id?: number }) {
  return apiRequest<Medicine[]>(endpoints.medicines.list, {
    params: {
      ...(params?.q ? { q: params.q } : {}),
      ...(params?.category_id !== undefined ? { category_id: params.category_id } : {}),
    },
  })
}

export function listCategoriesRequest() {
  return apiRequest<MedicineCategory[]>(endpoints.medicines.categories)
}

export function createMedicineRequest(body: {
  name: string
  generic_name?: string
  category_id: number
  dosage_form?: string
  strength?: string
  barcode?: string
  reorder_level: number
}) {
  return apiRequest<Medicine>(endpoints.medicines.list, { method: 'POST', body })
}

export function listMedicineBatchesRequest(medicineId: number) {
  return apiRequest<MedicineBatch[]>(endpoints.medicines.batches(medicineId))
}