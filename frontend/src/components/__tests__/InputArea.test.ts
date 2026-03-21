import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import InputArea from '../InputArea.vue'

describe('InputArea', () => {
  it('renders textarea and send button', () => {
    const wrapper = mount(InputArea)
    expect(wrapper.find('textarea').exists()).toBe(true)
    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('emits send event when button clicked', async () => {
    const wrapper = mount(InputArea)
    const textarea = wrapper.find('textarea')
    await textarea.setValue('Hello')
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('send')).toBeTruthy()
    expect(wrapper.emitted('send')?.[0]).toEqual(['Hello'])
  })

  it('emits send event on Enter without Shift', async () => {
    const wrapper = mount(InputArea)
    const textarea = wrapper.find('textarea')
    await textarea.setValue('Hello')
    await textarea.trigger('keydown', { key: 'Enter', shiftKey: false })
    expect(wrapper.emitted('send')).toBeTruthy()
  })

  it('does not emit on Shift+Enter', async () => {
    const wrapper = mount(InputArea)
    const textarea = wrapper.find('textarea')
    await textarea.trigger('keydown', { key: 'Enter', shiftKey: true })
    expect(wrapper.emitted('send')).toBeFalsy()
  })

  it('disables when disabled prop is true', () => {
    const wrapper = mount(InputArea, { props: { disabled: true } })
    expect(wrapper.find('textarea').element.disabled).toBe(true)
  })
})
