import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import HomeView from './HomeView.vue'

describe('Página inicial', () => {
  it('apresenta a proposta do projeto com um título principal', () => {
    const wrapper = mount(HomeView)

    expect(wrapper.findAll('h1')).toHaveLength(1)
    expect(wrapper.get('h1').text()).toBe('Organize o trabalho. Simplifique o dia.')
    expect(wrapper.get('main').text()).toContain('TaskFlow')
  })

  it('informa que autenticação e tarefas ainda não estão disponíveis', () => {
    const wrapper = mount(HomeView)

    expect(wrapper.text()).toContain('serão implementados nas próximas etapas.')
    expect(wrapper.find('form').exists()).toBe(false)
  })
})
