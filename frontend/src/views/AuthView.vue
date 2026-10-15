<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { ArrowRight, Eye, EyeOff } from '@lucide/vue'
import BrandLogo from '../components/brand/BrandLogo.vue'
import AuthIllustration from '../components/brand/AuthIllustration.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import FormField from '../components/ui/FormField.vue'
import { useAuthStore } from '../stores/auth'
import { errorMessage } from '../api/client'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const mode = computed(() =>
  route.meta.mode === 'register' ? 'register' : 'login',
)
const form = reactive({ name: '', email: '', password: '', confirmation: '' })
const state = reactive({ error: '', showPassword: false, success: '' })

async function submit() {
  state.error = ''
  if (
    !form.email ||
    !form.password ||
    (mode.value === 'register' && !form.name)
  ) {
    state.error = 'Preencha todos os campos obrigatórios.'
    return
  }
  if (form.password.length < 8) {
    state.error = 'A senha deve ter pelo menos 8 caracteres.'
    return
  }
  if (mode.value === 'register' && form.password !== form.confirmation) {
    state.error = 'As senhas devem ser iguais.'
    return
  }
  try {
    if (mode.value === 'register') {
      await auth.register(form.name, form.email, form.password)
      await router.push('/login')
      state.success = 'Conta criada. Entre com seu e-mail e senha.'
      form.password = ''
      form.confirmation = ''
      return
    } else {
      await auth.login({ email: form.email, password: form.password })
    }
    await router.push((route.query.redirect as string) || '/app/dashboard')
  } catch (error) {
    state.error = errorMessage(error)
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-panel">
      <div class="auth-panel__inner">
        <BrandLogo />
        <div class="auth-copy">
          <h1>Transforme planos<br>em <em>progresso.</em></h1>
          <p>
            Organize prioridades, acompanhe prazos e mantenha todas as suas
            tarefas no fluxo certo.
          </p>
        </div>
        <AuthIllustration />
      </div>
    </section>

    <section class="auth-form-panel">
      <div class="auth-form-wrap">
        <div class="mobile-brand">
          <BrandLogo />
        </div>
        <span class="eyebrow">{{
          mode === 'login' ? 'Bem-vindo' : 'Comece agora'
        }}</span>
        <h2>
          {{
            mode === 'login' ? 'Entre na sua conta' : 'Crie sua conta grátis'
          }}
        </h2>
        <p
          v-if="route.query.expired"
          class="form-alert"
          role="alert"
        >
          Sua sessão expirou. Entre novamente.
        </p>
        <p
          v-if="auth.restoreError"
          class="form-alert"
          role="alert"
        >
          {{ auth.restoreError }}
        </p>
        <form
          class="auth-form"
          @submit.prevent="submit"
        >
          <FormField
            v-if="mode === 'register'"
            v-model="form.name"
            label="Nome"
            :maxlength="100"
            placeholder="Como podemos chamar você?"
            autocomplete="name"
            required
          />
          <FormField
            v-model="form.email"
            label="E-mail"
            :maxlength="254"
            type="email"
            placeholder="voce@empresa.com"
            autocomplete="email"
            required
          />
          <div class="password-field">
            <FormField
              v-model="form.password"
              label="Senha"
              :minlength="8"
              :maxlength="128"
              :type="state.showPassword ? 'text' : 'password'"
              placeholder="Mínimo de 8 caracteres"
              :autocomplete="
                mode === 'login' ? 'current-password' : 'new-password'
              "
              required
            />
            <button
              type="button"
              :aria-label="
                state.showPassword ? 'Ocultar senha' : 'Mostrar senha'
              "
              @click="state.showPassword = !state.showPassword"
            >
              <EyeOff
                v-if="state.showPassword"
                :size="19"
              />
              <Eye
                v-else
                :size="19"
              />
            </button>
          </div>
          <FormField
            v-if="mode === 'register'"
            v-model="form.confirmation"
            label="Confirmar senha"
            :minlength="8"
            :maxlength="128"
            type="password"
            autocomplete="new-password"
            required
          />
          <p
            v-if="state.success"
            role="status"
            class="success-message"
          >
            {{ state.success }}
          </p>
          <div
            v-if="state.error"
            class="form-alert"
            role="alert"
          >
            {{ state.error }}
          </div>
          <BaseButton
            type="submit"
            size="lg"
            block
            :loading="auth.loading"
          >
            {{ mode === 'login' ? 'Entrar no TaskFlow' : 'Criar minha conta' }}
            <ArrowRight :size="18" />
          </BaseButton>
        </form>

        <p class="auth-switch">
          {{
            mode === 'login' ? 'Ainda não tem uma conta?' : 'Já tem uma conta?'
          }}
          <RouterLink :to="mode === 'login' ? '/cadastro' : '/login'">
            {{ mode === 'login' ? 'Cadastre-se' : 'Entrar' }}
          </RouterLink>
        </p>
      </div>
    </section>
  </main>
</template>
