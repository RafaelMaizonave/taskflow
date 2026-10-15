import { ref } from 'vue'

export type DialogVariant = 'primary' | 'danger'

export type DialogRequest = {
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: DialogVariant
  mode: 'confirm' | 'alert'
  resolve: (value: boolean) => void
}

const dialog = ref<DialogRequest | null>(null)

function open(
  options: Omit<DialogRequest, 'resolve' | 'mode'> & {
    mode: DialogRequest['mode']
  },
): Promise<boolean> {
  return new Promise((resolve) => {
    dialog.value?.resolve(false)
    dialog.value = { ...options, resolve }
  })
}

export function useDialog() {
  function confirm(
    options: Omit<DialogRequest, 'resolve' | 'mode'>,
  ): Promise<boolean> {
    return open({
      confirmLabel: 'Confirmar',
      cancelLabel: 'Cancelar',
      variant: 'primary',
      ...options,
      mode: 'confirm',
    })
  }

  function alert(
    options: Omit<DialogRequest, 'resolve' | 'mode' | 'cancelLabel'>,
  ): Promise<void> {
    return open({
      confirmLabel: 'Entendi',
      variant: 'primary',
      ...options,
      mode: 'alert',
    }).then(() => undefined)
  }

  function close(result: boolean) {
    const current = dialog.value
    if (!current) return
    dialog.value = null
    current.resolve(result)
  }

  return { dialog, confirm, alert, close }
}
