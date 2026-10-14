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
api.interceptors.response.use(response => response, error => {
  if (error.response?.status === 401 && error.config?.headers?.Authorization && error.config.headers.Authorization === api.defaults.headers.common.Authorization) {
    useAuthStore(pinia).logout()
    void router.replace({ path: '/login', query: { expired: '1' } })
  }
  return Promise.reject(error)
})
app.use(router).mount('#app')
