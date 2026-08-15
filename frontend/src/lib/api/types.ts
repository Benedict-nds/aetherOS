export type ApiResponse<T> = {
  success: boolean
  data: T
  message?: string
  errors?: string[]
}
