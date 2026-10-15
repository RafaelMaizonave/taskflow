<script setup lang="ts">
import { nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { X } from '@lucide/vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import FormField from '../../components/ui/FormField.vue'
import { useTasksStore } from '../../stores/tasks'
import { useToasts } from '../../composables/useToasts'
import type { Task, TaskInput } from '../../types'

const props = defineProps<{ open: boolean; task?: Task | null }>()
const emit = defineEmits<{ 'update:open': [value: boolean] }>()
const drawer = ref<HTMLElement | null>(null)
let previousFocus: HTMLElement | null = null
function keydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && !state.saving) emit('update:open', false)
  if (event.key !== 'Tab') return
  const elements = drawer.value?.querySelectorAll<HTMLElement>(
    'button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled)',
  )
  if (!elements?.length) return
  const first = elements[0]!
  const last = elements[elements.length - 1]!
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}
watch(
  () => props.open,
  async (open) => {
    if (open) {
      previousFocus = document.activeElement as HTMLElement
      document.body.style.overflow = 'hidden'
      document.addEventListener('keydown', keydown)
      await nextTick()
      drawer.value?.querySelector<HTMLInputElement>('input')?.focus()
    } else {
      document.body.style.overflow = ''
      document.removeEventListener('keydown', keydown)
      previousFocus?.focus()
    }
  },
)
onBeforeUnmount(() => {
  document.body.style.overflow = ''
  document.removeEventListener('keydown', keydown)
})
const tasks = useTasksStore()
const { show } = useToasts()

type TaskFormState = Omit<TaskInput, 'description' | 'due_date'> & {
  description: string
  due_date: string
}

const form = reactive<TaskFormState>({
  title: '',
  description: '',
  status: 'backlog',
  priority: 'medium',
  due_date: '',
  tags: [],
})
const state = reactive({ error: '', saving: false, tagsText: '' })

watch(
  () => [props.open, props.task] as const,
  () => {
    if (!props.open) return
    form.title = props.task?.title || ''
    form.description = props.task?.description || ''
    form.status = props.task?.status || 'backlog'
    form.priority = props.task?.priority || 'medium'
    form.due_date = props.task?.due_date || ''
    form.tags = props.task?.tags || []
    state.tagsText = form.tags.join(', ')
    state.error = ''
  },
  { immediate: true },
)

async function submit() {
  if (!form.title.trim()) {
    state.error = 'Dê um título para a tarefa.'
    return
  }
  state.error = ''
  form.tags = state.tagsText
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
  if (form.title.trim().length > 200 || form.description.length > 10000) {
    state.error = 'Use até 200 caracteres no título e 10.000 na descrição.'
    return
  }
  if (form.tags.length > 6 || form.tags.some((tag) => tag.length > 40)) {
    state.error = 'Use até 6 tags, com no máximo 40 caracteres cada.'
    return
  }
  state.saving = true
  try {
    const payload: TaskInput = {
      ...form,
      title: form.title.trim(),
      description: form.description || null,
      due_date: form.due_date || null,
    }
    if (props.task) {
      await tasks.update(props.task.id, payload)
      show('Tarefa atualizada.')
    } else {
      await tasks.create(payload)
      show('Tarefa criada com sucesso.')
    }
    emit('update:open', false)
  } catch {
    show('Não foi possível salvar a tarefa.', 'error')
  } finally {
    state.saving = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="drawer-layer"
      role="presentation"
    >
      <div
        class="drawer-scrim"
        @click="!state.saving && emit('update:open', false)"
      />
      <section
        ref="drawer"
        class="task-drawer"
        role="dialog"
        aria-modal="true"
        :aria-label="task ? 'Editar tarefa' : 'Nova tarefa'"
      >
        <header class="task-drawer__header">
          <div>
            <span class="eyebrow">{{
              task ? 'Detalhes da tarefa' : 'Organize o próximo passo'
            }}</span>
            <h2>{{ task ? 'Editar tarefa' : 'Nova tarefa' }}</h2>
          </div>
          <button
            class="icon-btn"
            type="button"
            aria-label="Fechar"
            @click="emit('update:open', false)"
          >
            <X :size="20" />
          </button>
        </header>
        <form
          class="task-form"
          @submit.prevent="submit"
        >
          <fieldset
            :disabled="state.saving"
            class="task-form-fields"
          >
            <FormField
              v-model="form.title"
              label="Título"
              :maxlength="200"
              placeholder="Ex.: Revisar planejamento da sprint"
              required
              :error="state.error"
            />
            <FormField
              v-model="form.description"
              label="Descrição"
              :maxlength="10000"
              placeholder="Adicione contexto, links ou observações..."
              multiline
            />
            <div class="form-grid">
              <label class="field">
                <span class="field__label">Status</span>
                <select
                  v-model="form.status"
                  class="field__control"
                >
                  <option value="backlog">Backlog</option>
                  <option value="in_progress">Em andamento</option>
                  <option value="done">Concluída</option>
                </select>
              </label>
              <label class="field">
                <span class="field__label">Prioridade</span>
                <select
                  v-model="form.priority"
                  class="field__control"
                >
                  <option value="low">Baixa</option>
                  <option value="medium">Média</option>
                  <option value="high">Alta</option>
                </select>
              </label>
            </div>
            <FormField
              v-model="form.due_date"
              label="Prazo"
              type="date"
            />
            <FormField
              v-model="state.tagsText"
              label="Tags"
              placeholder="Produto, Design, Pesquisa"
            />
            <p class="form-hint">
              Separe as tags por vírgulas. Use até 6 tags.
            </p>
            <footer class="task-drawer__footer">
              <BaseButton
                variant="secondary"
                @click="emit('update:open', false)"
              >
                Cancelar
              </BaseButton>
              <BaseButton
                type="submit"
                :loading="state.saving"
              >
                {{ task ? 'Salvar alterações' : 'Criar tarefa' }}
              </BaseButton>
            </footer>
          </fieldset>
        </form>
      </section>
    </div>
  </Teleport>
</template>
