<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import {
  AtSign,
  CalendarDays,
  LogOut,
  ShieldCheck,
  UserRound,
} from '@lucide/vue'
import BaseButton from '../components/ui/BaseButton.vue'
import FormField from '../components/ui/FormField.vue'
import { useAuthStore } from '../stores/auth'
import { authApi } from '../api/auth'
import { errorMessage } from '../api/client'
const auth = useAuthStore()
const router = useRouter()
const form = reactive({
  name: auth.user?.name || '',
  email: auth.user?.email || '',
  current_password: '',
  password: '',
  confirmation: '',
})
const state = reactive({
  saving: false,
  changing: false,
  error: '',
  message: '',
})
const memberSince = computed(() =>
  auth.user?.created_at
    ? new Intl.DateTimeFormat('pt-BR', {
        month: 'long',
        year: 'numeric',
      }).format(new Date(auth.user.created_at))
    : 'Data não disponível',
)
async function save() {
  if (
    !form.name.trim() ||
    form.name.trim().length > 100 ||
    form.email.length > 254
  ) {
    state.error =
      'Informe um nome de até 100 caracteres e um e-mail de até 254 caracteres.'
    return
  }
  state.saving = true
  state.error = ''
  state.message = ''
  try {
    auth.user = await authApi.update({ name: form.name, email: form.email })
    state.message = 'Perfil atualizado.'
  } catch (error) {
    state.error = errorMessage(error)
  } finally {
    state.saving = false
  }
}
async function changePassword() {
  state.error = ''
  state.message = ''
  if (form.password !== form.confirmation) {
    state.error = 'As senhas devem ser iguais.'
    return
  }
  if (form.password.length < 8 || form.password.length > 128) {
    state.error = 'A nova senha deve ter entre 8 e 128 caracteres.'
    return
  }
  state.changing = true
  try {
    await authApi.changePassword({
      current_password: form.current_password,
      password: form.password,
    })
    form.current_password = ''
    form.password = ''
    form.confirmation = ''
    state.message = 'Senha alterada.'
  } catch (error) {
    state.error = errorMessage(error)
  } finally {
    state.changing = false
  }
}
async function logout() {
  try { await auth.logout(); await router.push('/login') }
  catch (error) { state.error = errorMessage(error) }
}
</script>
<template>
  <div class="profile-page">
    <header class="page-header">
      <div>
        <span class="eyebrow">Configurações</span>
        <h1>Meu perfil</h1>
        <p>Suas informações e preferências de conta.</p>
      </div>
    </header>
    <section class="profile-card">
      <div class="profile-hero">
        <span class="avatar avatar--large">{{ auth.initials }}</span>
        <div>
          <h2>{{ auth.user?.name }}</h2>
          <p>{{ auth.user?.email }}</p>
        </div>
        <span class="account-pill"><ShieldCheck :size="15" /> Conta protegida</span>
      </div>
      <div class="profile-details">
        <div>
          <span><UserRound :size="18" /> Nome</span><strong>{{ auth.user?.name }}</strong>
        </div>
        <div>
          <span><AtSign :size="18" /> E-mail</span><strong>{{ auth.user?.email }}</strong>
        </div>
        <div>
          <span><CalendarDays :size="18" /> Membro desde</span><strong>{{ memberSince }}</strong>
        </div>
      </div>
      <div class="profile-forms">
        <div
          v-if="state.error"
          class="form-alert"
          role="alert"
        >
          {{ state.error }}
        </div>
        <p
          v-if="state.message"
          class="success-message"
          role="status"
        >
          {{ state.message }}
        </p>
        <form
          class="auth-form"
          @submit.prevent="save"
        >
          <h2>Informações pessoais</h2>
          <FormField
            v-model="form.name"
            label="Nome"
            :maxlength="100"
            autocomplete="name"
            required
          /><FormField
            v-model="form.email"
            label="E-mail"
            :maxlength="254"
            type="email"
            autocomplete="email"
            required
          /><BaseButton
            type="submit"
            :loading="state.saving"
          >
            Salvar perfil
          </BaseButton>
        </form>
        <form
          class="auth-form"
          @submit.prevent="changePassword"
        >
          <h2>Alterar senha</h2>
          <FormField
            v-model="form.current_password"
            label="Senha atual"
            :minlength="8"
            :maxlength="128"
            type="password"
            autocomplete="current-password"
            required
          /><FormField
            v-model="form.password"
            label="Nova senha"
            :minlength="8"
            :maxlength="128"
            type="password"
            autocomplete="new-password"
            required
          /><FormField
            v-model="form.confirmation"
            label="Confirmar nova senha"
            :minlength="8"
            :maxlength="128"
            type="password"
            autocomplete="new-password"
            required
          /><BaseButton
            type="submit"
            :loading="state.changing"
          >
            Alterar senha
          </BaseButton>
        </form>
      </div>
      <div class="profile-footer">
        <div>
          <strong>Sair desta conta</strong>
          <p>Você poderá entrar novamente a qualquer momento.</p>
        </div>
        <BaseButton
          variant="danger"
          @click="logout"
        >
          <LogOut :size="17" /> Sair
        </BaseButton>
      </div>
    </section>
  </div>
</template>
