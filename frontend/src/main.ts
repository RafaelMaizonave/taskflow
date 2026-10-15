import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { api } from './api/client'
import { useAuthStore } from './stores/auth'
import './style.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
api.interceptors.request.use(config => {
  config.sessionVersion = useAuthStore(pinia).sessionVersion
  return config
})
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const auth = useAuthStore(pinia)
    if (error.response?.status === 401 && auth.isAuthenticated && error.config?.sessionVersion === auth.sessionVersion && !error.config?.url?.startsWith('/auth/login')) {
      auth.clearSession()
      void router.replace({ path: '/login', query: { expired: '1' } })
    }
    return Promise.reject(error)
  },
)
app.use(router).mount('#app')
