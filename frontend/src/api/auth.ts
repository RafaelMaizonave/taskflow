import { api } from './client'
import type { User } from '../types'

export interface Credentials { email: string; password: string }
interface TokenResponse { access_token: string; token_type: string; expires_in: number }
export const authApi = {
  async register(data: Credentials) { return (await api.post<User>('/auth/register', data)).data },
  async login(data: Credentials) { return (await api.post<TokenResponse>('/auth/login', data)).data },
  async me() { return (await api.get<User>('/auth/me')).data },
}
