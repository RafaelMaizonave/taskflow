import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AuthView from '../views/AuthView.vue'
import DashboardView from '../views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/tarefas' },
    { path: '/login', component: AuthView, props: { mode: 'login' } },
    { path: '/cadastro', component: AuthView, props: { mode: 'register' } },
    { path: '/tarefas', component: DashboardView, meta: { requiresAuth: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.authenticated) return '/login'
  if (['/login', '/cadastro'].includes(to.path) && auth.authenticated) return '/tarefas'
})

export default router
