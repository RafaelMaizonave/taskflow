<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { statusLabels, type Task, type TaskInput, type TaskStatus } from '../types'

const props = defineProps<{ task: Task | null; busy: boolean }>()
const emit = defineEmits<{ save: [data: TaskInput]; cancel: [] }>()
const titulo = ref(props.task?.titulo || '')
const descricao = ref(props.task?.descricao || '')
const status = ref<TaskStatus>(props.task?.status || 'pending')
const titleInput = ref<HTMLInputElement>()
const error = ref('')
onMounted(() => titleInput.value?.focus())
function submit() {
  if (!titulo.value.trim()) { error.value = 'Informe um título para a tarefa.'; return }
  error.value = ''
  emit('save', { titulo: titulo.value.trim(), descricao: descricao.value, status: status.value })
}
</script>

<template>
  <section
    class="editor card"
    aria-labelledby="editor-title"
  >
    <h2 id="editor-title">
      {{ task ? 'Editar tarefa' : 'Nova tarefa' }}
    </h2>
    <p
      v-if="error"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>
    <form
      class="stack"
      @submit.prevent="submit"
    >
      <div class="field">
        <label for="task-title">Título</label>
        <input
          id="task-title"
          ref="titleInput"
          v-model="titulo"
          required
          maxlength="200"
          :disabled="busy"
          placeholder="Qual é o próximo passo?"
        >
      </div>
      <div class="field">
        <label for="task-description">Descrição <span class="muted">(opcional)</span></label>
        <textarea
          id="task-description"
          v-model="descricao"
          rows="3"
          maxlength="10000"
          :disabled="busy"
          placeholder="Adicione os detalhes que fazem a diferença"
        />
      </div>
      <div class="field">
        <label for="task-status">Status</label>
        <select
          id="task-status"
          v-model="status"
          :disabled="busy"
        >
          <option
            v-for="(label, value) in statusLabels"
            :key="value"
            :value="value"
          >
            {{ label }}
          </option>
        </select>
      </div>
      <div class="actions">
        <button
          class="button primary"
          type="submit"
          :disabled="busy"
        >
          {{ busy ? 'Salvando…' : 'Salvar tarefa' }}
        </button>
        <button
          class="button secondary"
          type="button"
          :disabled="busy"
          @click="emit('cancel')"
        >
          Cancelar
        </button>
      </div>
    </form>
  </section>
</template>
