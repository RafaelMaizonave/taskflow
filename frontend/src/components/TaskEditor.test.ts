import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import TaskEditor from './TaskEditor.vue'
import type { Task } from '../types'

const task: Task = { id: 1, titulo: 'Original', descricao: 'Detalhes', status: 'pending', user_id: 1, data_criacao: '2026-10-14T12:00:00Z' }

describe('Formulário de tarefa', () => {
  it('envia os campos editados sem identidade ou proprietário', async () => {
    const wrapper = mount(TaskEditor, { props: { task, busy: false } })
    await wrapper.get('#task-title').setValue('  Revisada  ')
    await wrapper.get('#task-status').setValue('completed')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.emitted('save')).toEqual([[{ titulo: 'Revisada', descricao: 'Detalhes', status: 'completed' }]])
  })

  it('rejeita um título composto apenas por espaços', async () => {
    const wrapper = mount(TaskEditor, { props: { task: null, busy: false } })
    await wrapper.get('#task-title').setValue('   ')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.emitted('save')).toBeUndefined()
    expect(wrapper.get('[role="alert"]').text()).toContain('Informe um título')
  })

  it('bloqueia os controles durante a gravação', () => {
    const wrapper = mount(TaskEditor, { props: { task, busy: true } })
    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('#task-title').attributes('disabled')).toBeDefined()
  })
})
