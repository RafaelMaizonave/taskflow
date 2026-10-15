<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppDialog from './components/feedback/AppDialog.vue'
import ToastViewport from './components/feedback/ToastViewport.vue'
</script>

<template>
  <RouterView />
  <AppDialog />
  <ToastViewport />
</template>
