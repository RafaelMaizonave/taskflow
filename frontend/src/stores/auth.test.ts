import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { authApi } from '../api/auth'
import { api } from '../api/client'
import { useAuthStore } from './auth'

vi.mock('../api/auth', () => ({ authApi: { login: vi.fn(), logout: vi.fn(), me: vi.fn() } }))
const user = { id: 1, email: 'user@example.com', name: 'Usuário', created_at: null }
beforeEach(() => { setActivePinia(createPinia()); vi.resetAllMocks() })

describe('Sessão por cookie HttpOnly', () => {
  it('autentica sem persistir credenciais no armazenamento acessível a JavaScript', async () => {
    vi.mocked(authApi.me).mockResolvedValue(user)
    const store = useAuthStore()
    await store.login({ email: user.email, password: 'test-password' })
    expect(store.authenticated).toBe(true)
    expect(api.defaults.withCredentials).toBe(true)
    expect(api.defaults.headers.common.Authorization).toBeUndefined()
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
    await store.logout()
    expect(authApi.logout).toHaveBeenCalledOnce()
    expect(store.authenticated).toBe(false)
  })
  it('restaura a sessão uma vez antes de resolver a navegação', async () => {
    vi.mocked(authApi.me).mockResolvedValue(user)
    const store = useAuthStore()
    await Promise.all([store.initialize(), store.initialize()])
    expect(authApi.me).toHaveBeenCalledOnce()
    expect(store.user).toEqual(user)
    expect(store.initialized).toBe(true)
  })
  it('não restaura uma resposta antiga depois de limpar a sessão', async () => {
    let resolve!: (value: typeof user) => void
    vi.mocked(authApi.me).mockReturnValue(new Promise(done => { resolve = done }))
    const store = useAuthStore()
    const restoring = store.initialize()
    store.clearSession()
    resolve(user)
    await restoring
    expect(store.authenticated).toBe(false)
  })
  it('não autentica quando a consulta do usuário falha', async () => {
    vi.mocked(authApi.me).mockRejectedValue(new Error('Sem sessão'))
    const store = useAuthStore()
    await expect(store.login({ email: user.email, password: 'test-password' })).rejects.toThrow()
    expect(store.authenticated).toBe(false)
  })
})
