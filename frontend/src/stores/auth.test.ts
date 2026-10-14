import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { authApi } from '../api/auth'
import { api } from '../api/client'
import { useAuthStore } from './auth'

vi.mock('../api/auth', () => ({ authApi: { login: vi.fn(), me: vi.fn() } }))

beforeEach(() => {
  setActivePinia(createPinia())
  vi.resetAllMocks()
  delete api.defaults.headers.common.Authorization
})

describe('Sessão em memória', () => {
  it('autentica e envia o token, sem persistir credenciais', async () => {
    vi.mocked(authApi.login).mockResolvedValue({ access_token: 'test-token', token_type: 'bearer', expires_in: 1800 })
    vi.mocked(authApi.me).mockResolvedValue({ id: 1, email: 'user@example.com' })
    const store = useAuthStore()
    await store.login({ email: 'user@example.com', password: 'test-password' })
    expect(store.authenticated).toBe(true)
    expect(store.user?.email).toBe('user@example.com')
    expect(api.defaults.headers.common.Authorization).toBe('Bearer test-token')
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
    store.logout()
    expect(store.authenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(api.defaults.headers.common.Authorization).toBeUndefined()
  })

  it('descarta o token quando a consulta do usuário falha', async () => {
    vi.mocked(authApi.login).mockResolvedValue({ access_token: 'test-token', token_type: 'bearer', expires_in: 1800 })
    vi.mocked(authApi.me).mockRejectedValue(new Error('Sem sessão'))
    const store = useAuthStore()
    await expect(store.login({ email: 'user@example.com', password: 'test-password' })).rejects.toThrow()
    expect(store.authenticated).toBe(false)
    expect(api.defaults.headers.common.Authorization).toBeUndefined()
  })
})
