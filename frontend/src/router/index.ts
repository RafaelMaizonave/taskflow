import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AuthView from '../views/AuthView.vue'
import DashboardView from '../views/DashboardView.vue'
import TasksView from '../views/TasksView.vue'
import ProfileView from '../views/ProfileView.vue'
import NotFoundView from '../views/NotFoundView.vue'
import AppShell from '../components/layout/AppShell.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/tarefas', redirect: '/app/tarefas' },
    { path: '/', redirect: '/app/dashboard' },
    {
      path: '/login',
      component: AuthView,
      meta: { public: true, mode: 'login' },
    },
    {
      path: '/cadastro',
      component: AuthView,
      meta: { public: true, mode: 'register' },
    },
    {
      path: '/app',
      component: AppShell,
      children: [
        { path: '', redirect: '/app/dashboard' },
        { path: 'dashboard', component: DashboardView },
        { path: 'tarefas', component: TasksView },
        { path: 'perfil', component: ProfileView },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      component: NotFoundView,
      meta: { public: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.initialize()
  const isPublic = Boolean(to.meta.public)
  if (!isPublic && !auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (
    isPublic &&
    auth.isAuthenticated &&
    ['/login', '/cadastro'].includes(to.path)
  ) {
    return '/app/dashboard'
  }
})

export default router
