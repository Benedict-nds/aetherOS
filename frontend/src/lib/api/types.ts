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