import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { authApi, type Credentials } from '../api/auth'
import { setAccessToken } from '../api/client'
import type { User } from '../types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const authenticated = computed(() => Boolean(accessToken.value && user.value))

  function logout() {
    user.value = null
    accessToken.value = null
    setAccessToken(null)
  }

  async function login(credentials: Credentials) {
    logout()
    const response = await authApi.login(credentials)
    accessToken.value = response.access_token
    setAccessToken(response.access_token)
    try { user.value = await authApi.me() }
    catch (error) { logout(); throw error }
  }

  return { user, authenticated, login, logout }
})
