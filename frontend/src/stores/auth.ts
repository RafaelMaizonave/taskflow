import { computed, ref } from 'vue'
import axios from 'axios'
import { defineStore } from 'pinia'
import { authApi, type Credentials } from '../api/auth'
import { errorMessage } from '../api/client'
import { useTasksStore } from './tasks'
import type { User } from '../types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const initialized = ref(false)
  const loading = ref(false)
  const restoreError = ref('')
  const sessionVersion = ref(0)
  let restoring: Promise<void> | null = null
  const authenticated = computed(() => Boolean(user.value))
  const initials = computed(() =>
    (user.value?.name || user.value?.email || 'TF').split(' ').slice(0, 2)
      .map(part => part[0]).join('').toUpperCase(),
  )

  function clearSession() {
    sessionVersion.value++
    useTasksStore().reset()
    user.value = null
    initialized.value = true
    restoreError.value = ''
  }

  async function initialize() {
    if (initialized.value) return
    if (restoring) return restoring
    const current = sessionVersion.value
    restoring = (async () => {
      try {
        const restored = await authApi.me()
        if (current === sessionVersion.value) user.value = restored
      } catch (error) {
        if (current !== sessionVersion.value) return
        user.value = null
        if (!axios.isAxiosError(error) || error.response?.status !== 401) {
          restoreError.value = errorMessage(error)
        }
      } finally {
        if (current === sessionVersion.value) initialized.value = true
        restoring = null
      }
    })()
    return restoring
  }

  async function logout() {
    await authApi.logout()
    clearSession()
  }

  async function login(credentials: Credentials) {
    clearSession()
    loading.value = true
    try {
      await authApi.login(credentials)
      user.value = await authApi.me()
    } catch (error) {
      clearSession()
      throw error
    } finally {
      loading.value = false
    }
  }

  async function register(name: string, email: string, password: string) {
    loading.value = true
    try { await authApi.register({ name, email, password }) }
    finally { loading.value = false }
  }
  return {
    user, authenticated, isAuthenticated: authenticated, initials, loading,
    initialized, restoreError, sessionVersion, initialize, clearSession, login, logout, register,
  }
})
