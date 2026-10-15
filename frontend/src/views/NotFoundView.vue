<script setup lang="ts">
import { ArrowLeft } from '@lucide/vue'
import { RouterLink } from 'vue-router'
import BrandLogo from '../components/brand/BrandLogo.vue'
</script>

<template>
  <main class="not-found">
    <BrandLogo />
    <div class="not-found__art">
      <span>4</span><svg viewBox="0 0 100 100">
        <path d="M22 51h18l10-21 13 42 9-21h10" /></svg><span>4</span>
    </div>
    <h1>Este fluxo se perdeu</h1>
    <p>A página que você procura não existe ou mudou de lugar.</p>
    <RouterLink to="/app/dashboard">
      <ArrowLeft :size="17" /> Voltar ao dashboard
    </RouterLink>
  </main>
</template>
