import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import TaskFormDrawer from './TaskFormDrawer.vue'
import { useTasksStore } from '../../stores/tasks'
import type { VueWrapper } from '@vue/test-utils'
let wrapper: VueWrapper
beforeEach(() => {
  setActivePinia(createPinia())
})
afterEach(() => {
  wrapper?.unmount()
  document.body.innerHTML = ''
  document.body.style.overflow = ''
})
async function openDrawer() {
  const trigger = document.createElement('button')
  document.body.appendChild(trigger)
  trigger.focus()
  wrapper = mount(TaskFormDrawer, {
    props: { open: false },
    attachTo: document.body,
  })
  await wrapper.setProps({ open: true })
  await flushPromises()
  return trigger
}
describe('Edição acessível de tarefas', () => {
  it('foca título, mantém Tab no diálogo, fecha por Escape e restaura foco', async () => {
    const trigger = await openDrawer()
    expect(document.activeElement).toBe(document.querySelector('input'))
    const buttons = document.querySelectorAll<HTMLButtonElement>(
      '.task-drawer button',
    )
    const first = buttons[0]!
    const last = buttons[buttons.length - 1]!
    last.focus()
    document.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Tab', cancelable: true }),
    )
    expect(document.activeElement).toBe(first)
    first.focus()
    document.dispatchEvent(
      new KeyboardEvent('keydown', {
        key: 'Tab',
        shiftKey: true,
        cancelable: true,
      }),
    )
    expect(document.activeElement).toBe(last)
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('update:open')).toEqual([[false]])
    await wrapper.setProps({ open: false })
    expect(document.activeElement).toBe(trigger)
  })
  it('rejeita título vazio e tags excedentes sem descartá-las silenciosamente', async () => {
    const store = useTasksStore()
    const create = vi.spyOn(store, 'create')
    await openDrawer()
    const title = document.querySelector<HTMLInputElement>('#field-t-tulo')!
    title.value = '   '
    title.dispatchEvent(new Event('input', { bubbles: true }))
    document
      .querySelector('form')!
      .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flushPromises()
    expect(document.querySelector('[role="alert"]')?.textContent).toContain(
      'Dê um título',
    )
    title.value = 'Organizar'
    title.dispatchEvent(new Event('input', { bubbles: true }))
    const tags = document.querySelector<HTMLInputElement>('#field-tags')!
    tags.value = 'a,b,c,d,e,f,g,h,i,j,k'
    tags.dispatchEvent(new Event('input', { bubbles: true }))
    document
      .querySelector('form')!
      .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flushPromises()
    expect(document.querySelector('[role="alert"]')?.textContent).toContain(
      'até 10 tags',
    )
    expect(tags.value).toBe('a,b,c,d,e,f,g,h,i,j,k')
    expect(create).not.toHaveBeenCalled()
    tags.value = 'a'.repeat(41)
    tags.dispatchEvent(new Event('input', { bubbles: true }))
    document
      .querySelector('form')!
      .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flushPromises()
    expect(document.querySelector('[role="alert"]')?.textContent).toContain(
      '40 caracteres',
    )
    expect(create).not.toHaveBeenCalled()
  })
  it('expõe limites nativos alinhados ao banco', async () => {
    await openDrawer()
    expect(
      document.querySelector<HTMLInputElement>('#field-t-tulo')?.maxLength,
    ).toBe(200)
    expect(document.querySelector('textarea')?.maxLength).toBe(10000)
    expect(
      document.querySelector<HTMLInputElement>('#field-tags')?.maxLength,
    ).toBe(418)
  })
})
