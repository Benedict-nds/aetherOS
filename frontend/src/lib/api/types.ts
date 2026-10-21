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


export type StockStatus = 'healthy' | 'low' | 'critical'

export type LowStockRow = {
  medicine_id: number
  name: string
  category_name: string | null
  quantity_on_hand: number
  reorder_level: number
}

export type ExpiryBucket = 'expired' | '30' | '60' | '90'

export type ExpiryRow = {
  medicine_id: number
  name: string
  batch_id: number
  batch_number: string
  expiry_date: string
  quantity_on_hand: number
  bucket: ExpiryBucket
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
  quantity_on_hand: number
  nearest_batch_number: string | null
  nearest_expiry_date: string | null
  stock_status: StockStatus
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


export type DashboardSummary = {
  expiring_soon_count: number
  low_stock_count: number
  open_orders_count: number
  today_sales: {
    amount: number
    currency: string
  }
}

export type MedicineBatch = {
  id: number
  status: string
  quantity_on_hand: number
  expiry_date: string | null
  // may arrive as a decimal string depending on the serializer, so always wrap in Number()
  selling_price: number | string
}


export type SalePaymentMethod = 'cash' | 'momo' | 'card'


export type CreateSaleBody = {
  payment_method: SalePaymentMethod
  lines: { medicine_id: number; quantity: number }[]
}
