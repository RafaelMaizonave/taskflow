import { ref } from 'vue'

type Toast = { id: number; message: string; type: 'success' | 'error' }
const toasts = ref<Toast[]>([])
let id = 0

export function useToasts() {
  function show(message: string, type: Toast['type'] = 'success') {
    const toast = { id: ++id, message, type }
    toasts.value.push(toast)
    window.setTimeout(() => dismiss(toast.id), 4200)
  }

  function dismiss(toastId: number) {
    toasts.value = toasts.value.filter((toast) => toast.id !== toastId)
  }

  return { toasts, show, dismiss }
}
