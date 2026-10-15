<script setup lang="ts">
import { computed, onMounted } from 'vue'
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  CircleAlert,
  CircleDashed,
  ListTodo,
  Plus,
  TrendingUp,
} from '@lucide/vue'
import BaseButton from '../components/ui/BaseButton.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
import { useAuthStore } from '../stores/auth'
import { useTasksStore } from '../stores/tasks'

const emit = defineEmits<{ 'create-task': [] }>()
const auth = useAuthStore()
const tasks = useTasksStore()
const firstName = computed(() => auth.user?.name.split(' ')[0] || 'você')

const stats = computed(() => [
  {
    label: 'Total de tarefas',
    value: tasks.summary.total,
    icon: ListTodo,
    tone: 'violet',
    note: 'no seu fluxo',
  },
  {
    label: 'Em andamento',
    value: tasks.summary.in_progress,
    icon: CircleDashed,
    tone: 'blue',
    note: 'pedem atenção',
  },
  {
    label: 'Concluídas',
    value: tasks.summary.done,
    icon: CheckCircle2,
    tone: 'green',
    note: `${tasks.summary.completion_rate}% de progresso`,
  },
  {
    label: 'Atrasadas',
    value: tasks.summary.overdue,
    icon: CircleAlert,
    tone: 'coral',
    note: 'revise os prazos',
  },
])

function formatDate(value: string | null) {
  if (!value) return 'Sem prazo'
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: 'short',
  }).formatToParts(new Date(`${value}T12:00:00`))
    .filter(part => part.type === 'day' || part.type === 'month')
    .map(part => part.value)
    .join(' ')
}

onMounted(() => tasks.load())
</script>

<template>
  <div class="dashboard">
    <header class="page-header">
      <div>
        <span class="eyebrow">Visão geral</span>
        <h1>Olá, {{ firstName }}. Vamos avançar?</h1>
      </div>
      <BaseButton @click="emit('create-task')">
        <Plus :size="18" /> Nova tarefa
      </BaseButton>
    </header>

    <section
      class="stats-grid"
      aria-label="Resumo de tarefas"
    >
      <article
        v-for="stat in stats"
        :key="stat.label"
        class="stat-card"
      >
        <div class="stat-card__top">
          <span
            class="stat-icon"
            :class="`stat-icon--${stat.tone}`"
          ><component
            :is="stat.icon"
            :size="20"
          /></span>
        </div>
        <strong>{{ stat.value }}</strong>
        <span>{{ stat.label }}</span>
        <small>{{ stat.note }}</small>
      </article>
    </section>

    <section class="dashboard-grid">
      <article class="panel progress-panel">
        <div class="panel__header">
          <div>
            <span class="eyebrow">Seu progresso</span>
            <h2>Seu fluxo atual</h2>
          </div>
          <span class="trend-pill"><TrendingUp :size="15" /> Progresso atual</span>
        </div>
        <div class="progress-main">
          <div
            class="progress-ring"
            :style="{
              '--progress': `${tasks.summary.completion_rate * 3.6}deg`,
            }"
          >
            <div>
              <strong>{{ tasks.summary.completion_rate }}%</strong><span>concluído</span>
            </div>
          </div>
          <div class="progress-copy">
            <strong>Continue assim</strong>
            <p>
              Você concluiu {{ tasks.summary.done }} de
              {{ tasks.summary.total }} tarefas do seu fluxo atual.
            </p>
            <div class="progress-bar">
              <i :style="{ width: `${tasks.summary.completion_rate}%` }" />
            </div>
            <small>{{ tasks.summary.in_progress }} tarefas estão em andamento</small>
          </div>
        </div>
      </article>

      <article class="panel upcoming-panel">
        <div class="panel__header">
          <div>
            <span class="eyebrow">Agenda</span>
            <h2>Próximos prazos</h2>
          </div>
          <RouterLink to="/app/tarefas">
            Ver todas <ArrowRight :size="15" />
          </RouterLink>
        </div>
        <div
          v-if="tasks.loading"
          class="skeleton-list"
        >
          <i
            v-for="n in 3"
            :key="n"
          />
        </div>
        <div
          v-else-if="tasks.summary.upcoming.length"
          class="upcoming-list"
        >
          <div
            v-for="task in tasks.summary.upcoming"
            :key="task.id"
            class="upcoming-item"
          >
            <span class="date-tile">
              <CalendarDays
                :size="16"
                aria-hidden="true"
              />
              <time :datetime="task.due_date || undefined">{{ formatDate(task.due_date) }}</time>
            </span>
            <div>
              <strong>{{ task.title }}</strong><StatusBadge :value="task.priority" />
            </div>
          </div>
        </div>
        <div
          v-else
          class="compact-empty"
        >
          <CheckCircle2 :size="28" />
          <strong>Tudo em dia</strong>
          <span>Nenhum prazo próximo.</span>
        </div>
      </article>
    </section>
  </div>
</template>
