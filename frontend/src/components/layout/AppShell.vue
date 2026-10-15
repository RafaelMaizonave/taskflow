<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter, RouterLink, RouterView } from 'vue-router'
import {
  Bell,
  ChevronDown,
  LayoutDashboard,
  ListTodo,
  LogOut,
  Menu,
  Search,
  Settings,
  X,
} from '@lucide/vue'
import BrandLogo from '../../components/brand/BrandLogo.vue'
import TaskFormDrawer from '../../components/tasks/TaskFormDrawer.vue'
import { useToasts } from '../../composables/useToasts'
import { errorMessage } from '../../api/client'
import { useAuthStore } from '../../stores/auth'

import { useTasksStore, localDate } from '../../stores/tasks'
const tasks = useTasksStore()
const notificationsOpen = ref(false)
const notices = computed(() => {
  const next = new Date()
  next.setDate(next.getDate() + 3)
  return tasks.tasks
    .filter(
      (task) =>
        task.status !== 'done' &&
        task.due_date &&
        task.due_date <= localDate(next),
    )
    .sort((a, b) => a.due_date!.localeCompare(b.due_date!))
})
onMounted(() => tasks.load())
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const mobileOpen = ref(false)
const createOpen = ref(false)
const profileOpen = ref(false)

const profileMenu = ref<HTMLElement | null>(null)
const notificationsMenu = ref<HTMLElement | null>(null)
function closePopovers(event: KeyboardEvent | MouseEvent) {
  if (event instanceof KeyboardEvent) {
    if (event.key !== 'Escape') return
    profileOpen.value = false
    notificationsOpen.value = false
    mobileOpen.value = false
    return
  }
  const target = event.target as Node
  if (!profileMenu.value?.contains(target)) profileOpen.value = false
  if (!notificationsMenu.value?.contains(target))
    notificationsOpen.value = false
}
onMounted(() => {
  document.addEventListener('keydown', closePopovers)
  document.addEventListener('click', closePopovers)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', closePopovers)
  document.removeEventListener('click', closePopovers)
})
const links = [
  { to: '/app/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/app/tarefas', label: 'Minhas tarefas', icon: ListTodo },
]

async function logout() {
  try { await auth.logout(); await router.push('/login') }
  catch (error) { useToasts().show(errorMessage(error), 'error') }
}
</script>

<template>
  <div class="app-layout">
    <div
      v-if="mobileOpen"
      class="mobile-scrim"
      @click="mobileOpen = false"
    />
    <aside
      class="sidebar"
      :class="{ 'sidebar--open': mobileOpen }"
    >
      <div class="sidebar__brand">
        <BrandLogo />
        <button
          class="icon-btn sidebar__close"
          type="button"
          aria-label="Fechar menu"
          @click="mobileOpen = false"
        >
          <X :size="20" />
        </button>
      </div>
      <nav
        class="sidebar__nav"
        aria-label="Navegação principal"
      >
        <span class="sidebar__section">Organização</span>
        <RouterLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="sidebar__link"
          :class="{ 'sidebar__link--active': route.path === link.to }"
          @click="mobileOpen = false"
        >
          <component
            :is="link.icon"
            :size="19"
          />
          {{ link.label }}
        </RouterLink>
      </nav>
      <div class="sidebar__tip">
        <span>Seu ritmo hoje</span>
        <div><i :style="{ width: `${tasks.summary.completion_rate}%` }" /></div>
        <small>{{ tasks.summary.done }} de {{ tasks.summary.total }} tarefas
          concluídas</small>
      </div>
      <RouterLink
        to="/app/perfil"
        class="sidebar__profile"
        aria-label="Meu perfil"
        @click="mobileOpen = false"
      >
        <span class="avatar">{{ auth.initials }}</span>
        <span><strong>{{ auth.user?.name }}</strong><small>{{ auth.user?.email }}</small></span>
        <Settings :size="17" />
      </RouterLink>
    </aside>

    <section class="app-content">
      <header class="topbar">
        <button
          class="icon-btn mobile-menu"
          type="button"
          aria-label="Abrir menu"
          :aria-expanded="mobileOpen"
          @click="mobileOpen = true"
        >
          <Menu :size="21" />
        </button>
        <div class="topbar__search">
          <Search :size="18" />
          <input
            v-model="tasks.search"
            aria-label="Buscar em todo o TaskFlow"
            placeholder="Buscar tarefas ou tags"
            @input="router.push('/app/tarefas')"
          >
        </div>
        <div class="topbar__actions">
          <div
            ref="notificationsMenu"
            class="profile-menu"
          >
            <button
              class="icon-btn notification-btn"
              type="button"
              aria-label="Notificações"
              :aria-expanded="notificationsOpen"
              @click="notificationsOpen = !notificationsOpen"
            >
              <Bell :size="20" /><i v-if="notices.length" />
            </button>
            <div
              v-if="notificationsOpen"
              class="profile-popover notifications-popover"
            >
              <strong>Prazos próximos e vencidos</strong>
              <p v-if="!notices.length">
                Nenhum aviso de prazo.
              </p>
              <RouterLink
                v-for="task in notices"
                :key="task.id"
                to="/app/tarefas"
                @click="notificationsOpen = false"
              >
                <span>{{ task.title
                }}<small>{{
                  task.due_date! < localDate()
                    ? 'Prazo vencido'
                    : 'Prazo próximo'
                }}
                  · {{ task.due_date?.split('-').reverse().join('/') }}</small></span>
              </RouterLink>
            </div>
          </div>
          <div
            ref="profileMenu"
            class="profile-menu"
          >
            <button
              class="profile-trigger"
              aria-label="Abrir menu do perfil"
              :aria-expanded="profileOpen"
              type="button"
              @click="profileOpen = !profileOpen"
            >
              <span class="avatar avatar--small">{{ auth.initials }}</span>
              <ChevronDown :size="15" />
            </button>
            <div
              v-if="profileOpen"
              class="profile-popover"
            >
              <RouterLink
                to="/app/perfil"
                @click="profileOpen = false"
              >
                <Settings :size="16" /> Meu perfil
              </RouterLink>
              <button
                type="button"
                @click="logout"
              >
                <LogOut :size="16" /> Sair
              </button>
            </div>
          </div>
        </div>
      </header>
      <main class="page-content">
        <div
          v-if="tasks.error"
          class="form-alert"
          role="alert"
        >
          {{ tasks.error }}
          <button
            type="button"
            @click="tasks.load(true)"
          >
            Tentar novamente
          </button>
        </div>
        <RouterView @create-task="createOpen = true" />
      </main>
    </section>
    <TaskFormDrawer v-model:open="createOpen" />
  </div>
</template>
