export type ApiResponse<T> = {
  success: boolean
  data: T | null
  message: string
  errors: string[]
}


export type AuthUser = {
  id: number
  full_name: string
  email: string
  username: string
  role: string
}


export type LoginData = {
  access_token: string
  token_type: string
  user: AuthUser
}


export type Medicine = {
  id: number
  name: string
  generic_name: string | null
  brand_name: string | null
  category_id: number | null
  category_name: string | null
  barcode: string | null
  dosage_form: string | null
  strength: string | null
  unit: string | null
  reorder_level: number
  is_active: boolean
  created_at: string
  updated_at: string
}


export type MedicineCategory = {
  id: number
  name: string
  description: string | null
  status: string
  created_at: string
}