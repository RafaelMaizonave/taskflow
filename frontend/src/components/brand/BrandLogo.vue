<script setup lang="ts">
withDefaults(defineProps<{ compact?: boolean; light?: boolean }>(), {
  compact: false,
  light: false,
})
</script>

<template>
  <div
    class="brand"
    :class="{ 'brand--light': light }"
    aria-label="TaskFlow"
  >
    <svg
      class="brand__mark"
      viewBox="0 0 40 40"
      aria-hidden="true"
    >
      <rect
        width="40"
        height="40"
        rx="12"
        fill="currentColor"
      />
      <path
        d="M11 20.5l5.5 5.5L29 13.5"
        fill="none"
        stroke="white"
        stroke-width="4"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path
        d="M11 13.5h7"
        fill="none"
        stroke="white"
        stroke-width="3"
        stroke-linecap="round"
        opacity=".72"
      />
    </svg>
    <span
      v-if="!compact"
      class="brand__word"
    >Task<span>Flow</span></span>
  </div>
</template>
