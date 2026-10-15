import { beforeEach, describe, expect, it } from 'vitest'
import { useDialog } from './useDialog'

describe('useDialog', () => {
  const { dialog, confirm, alert, close } = useDialog()

  beforeEach(() => {
    if (dialog.value) close(false)
  })

  it('abre confirmação e resolve true ao confirmar', async () => {
    const pending = confirm({
      title: 'Excluir tarefa',
      message: 'Confirma?',
      variant: 'danger',
    })
    expect(dialog.value?.mode).toBe('confirm')
    expect(dialog.value?.title).toBe('Excluir tarefa')
    close(true)
    await expect(pending).resolves.toBe(true)
    expect(dialog.value).toBeNull()
  })

  it('resolve false ao cancelar confirmação', async () => {
    const pending = confirm({ title: 'Atenção', message: 'Sair?' })
    close(false)
    await expect(pending).resolves.toBe(false)
  })

  it('abre alerta sem cancelar e resolve ao confirmar', async () => {
    const pending = alert({ title: 'Aviso', message: 'Salvo.' })
    expect(dialog.value?.mode).toBe('alert')
    close(true)
    await expect(pending).resolves.toBeUndefined()
    expect(dialog.value).toBeNull()
  })
})
