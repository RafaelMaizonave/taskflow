<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
const router = useRouter()
function logout() {
  auth.logout()
  void router.push('/login')
}
</script>

<template>
  <main class="auth-panel">
    <section class="auth-card stack">
      <span class="eyebrow">TASKFLOW</span>
      <h1>Sua conta</h1>
      <p>{{ auth.user?.email }}</p>
      <p class="muted">
        Sua sessão está ativa. O gerenciamento de tarefas será disponibilizado na issue #7.
      </p>
      <button
        class="button secondary"
        @click="logout"
      >
        Sair
      </button>
    </section>
  </main>
</template>
