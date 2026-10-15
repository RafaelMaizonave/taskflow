<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    label: string
    type?: string
    placeholder?: string
    autocomplete?: string
    error?: string
    required?: boolean
    multiline?: boolean
    minlength?: number
    maxlength?: number
  }>(),
  {
    modelValue: '',
    type: 'text',
    multiline: false,
    placeholder: '',
    autocomplete: undefined,
    error: '',
    minlength: undefined,
    maxlength: undefined,
  },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const fieldId = computed(
  () => `field-${props.label.toLowerCase().replace(/\W+/g, '-')}`,
)
</script>

<template>
  <label
    class="field"
    :for="fieldId"
  >
    <span class="field__label">{{ label }} <b
      v-if="required"
      aria-hidden="true"
    >*</b></span>
    <textarea
      v-if="multiline"
      :id="fieldId"
      class="field__control field__control--textarea"
      :class="{ 'field__control--error': error }"
      :value="modelValue"
      :required="required"
      :minlength="minlength"
      :maxlength="maxlength"
      :aria-invalid="error ? true : undefined"
      :aria-describedby="error ? `${fieldId}-error` : undefined"
      :placeholder="placeholder"
      @input="
        emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)
      "
    />
    <input
      v-else
      :id="fieldId"
      class="field__control"
      :class="{ 'field__control--error': error }"
      :value="modelValue"
      :type="type"
      :required="required"
      :minlength="minlength"
      :maxlength="maxlength"
      :aria-invalid="error ? true : undefined"
      :aria-describedby="error ? `${fieldId}-error` : undefined"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      @input="
        emit('update:modelValue', ($event.target as HTMLInputElement).value)
      "
    >
    <span
      v-if="error"
      :id="`${fieldId}-error`"
      class="field__error"
      role="alert"
    >{{ error }}</span>
  </label>
</template>
