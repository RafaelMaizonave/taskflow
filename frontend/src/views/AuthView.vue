<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { authApi } from '../api/auth'
import { errorMessage } from '../api/client'
import { useAuthStore } from '../stores/auth'

const props = defineProps<{ mode: 'login' | 'register' }>()
const register = computed(() => props.mode === 'register')
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const email = ref('')
const password = ref('')
const confirmation = ref('')
const busy = ref(false)
const error = ref('')
watch(() => props.mode, () => { error.value = ''; password.value = ''; confirmation.value = '' })

async function submit() {
  if (busy.value) return
  error.value = ''
  if (register.value && password.value !== confirmation.value) {
    error.value = 'As senhas não coincidem.'
    return
  }
  busy.value = true
  try {
    const credentials = { email: email.value.trim(), password: password.value }
    if (register.value) {
      await authApi.register(credentials)
      password.value = ''; confirmation.value = ''
      await router.push({ path: '/login', query: { registered: '1' } })
    } else {
      await auth.login(credentials)
      password.value = ''
      await router.push('/tarefas')
    }
  } catch (cause) { error.value = errorMessage(cause) }
  finally { busy.value = false }
}
</script>

<template>
  <main class="auth-layout">
    <aside
      class="auth-story"
      aria-label="TaskFlow"
    >
      <a
        class="brand"
        href="/"
      >◈ <span>TaskFlow</span></a>
      <div>
        <span class="eyebrow">MENOS RUÍDO. MAIS CLAREZA.</span>
        <h1>Organize o trabalho.<br><span>Simplifique o dia.</span></h1>
        <p>Um espaço para transformar suas ideias em próximos passos. No seu ritmo, uma tarefa de cada vez.</p>
        <div class="story-note">
          <span class="note-check">✓</span> Seu próximo passo começa aqui.
        </div>
      </div>
      <p class="story-footer">
        Foco no que importa.
      </p>
    </aside>
    <section class="auth-panel">
      <div class="auth-card">
        <span class="eyebrow">BEM-VINDO AO SEU ESPAÇO</span>
        <h2>{{ register ? 'Crie sua conta' : 'Bom ter você de volta' }}</h2>
        <p class="muted">
          {{ register ? 'Comece a organizar suas tarefas em poucos passos.' : 'Entre para continuar de onde parou.' }}
        </p>
        <p
          v-if="route.query.registered && !register"
          class="notice success"
          role="status"
        >
          Conta criada! Entre com seu e-mail e senha.
        </p>
        <p
          v-if="route.query.expired && !register"
          class="notice"
          role="status"
        >
          Sua sessão expirou. Entre novamente.
        </p>
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
            <label for="email">E-mail</label>
            <input
              id="email"
              v-model="email"
              type="email"
              autocomplete="email"
              required
              maxlength="254"
              placeholder="voce@exemplo.com"
              :disabled="busy"
            >
          </div>
          <div class="field">
            <label for="password">Senha</label>
            <input
              id="password"
              v-model="password"
              type="password"
              :autocomplete="register ? 'new-password' : 'current-password'"
              required
              minlength="8"
              maxlength="128"
              placeholder="Pelo menos 8 caracteres"
              :disabled="busy"
            >
          </div>
          <div
            v-if="register"
            class="field"
          >
            <label for="confirmation">Confirmar senha</label>
            <input
              id="confirmation"
              v-model="confirmation"
              type="password"
              autocomplete="new-password"
              required
              minlength="8"
              maxlength="128"
              :disabled="busy"
            >
          </div>
          <button
            class="button primary full"
            type="submit"
            :disabled="busy"
          >
            {{ busy ? 'Aguarde…' : register ? 'Criar conta' : 'Entrar' }} <span aria-hidden="true">→</span>
          </button>
        </form>
        <p class="auth-switch">
          {{ register ? 'Já tem uma conta?' : 'Ainda não tem uma conta?' }} <RouterLink :to="register ? '/login' : '/cadastro'">
            {{ register ? 'Entrar' : 'Criar conta' }}
          </RouterLink>
        </p>
      </div>
    </section>
  </main>
</template>
