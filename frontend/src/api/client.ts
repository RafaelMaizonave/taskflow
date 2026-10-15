import axios from 'axios'

declare module 'axios' {
  interface AxiosRequestConfig { sessionVersion?: number }
}

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  withCredentials: true,
  headers: { 'X-Requested-With': 'XMLHttpRequest' },
})

export function errorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return 'Não foi possível concluir a operação.'
  if (!error.response)
    return 'Não foi possível conectar ao servidor. Tente novamente.'
  const detail: unknown = error.response.data?.detail
  if (typeof detail === 'string') return detail
  if (error.response.status === 422)
    return 'Confira os campos informados e tente novamente.'
  if (error.response.status === 401)
    return 'Sua sessão expirou. Entre novamente.'
  return 'Não foi possível concluir a operação. Tente novamente.'
}
