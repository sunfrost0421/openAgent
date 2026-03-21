import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageBubble from '../MessageBubble.vue'

describe('MessageBubble', () => {
  it('renders user message with correct class', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        message: {
          id: '1',
          role: 'user',
          content: 'Hello',
          createdAt: new Date(),
        },
      },
    })
    expect(wrapper.classes()).toContain('message')
    expect(wrapper.classes()).toContain('user')
  })

  it('renders AI message with correct class', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        message: {
          id: '1',
          role: 'ai',
          content: 'Hi',
          createdAt: new Date(),
        },
      },
    })
    expect(wrapper.classes()).toContain('message')
    expect(wrapper.classes()).toContain('ai')
  })

  it('displays message content', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        message: {
          id: '1',
          role: 'user',
          content: 'Test message',
          createdAt: new Date(),
        },
      },
    })
    expect(wrapper.text()).toContain('Test message')
  })
})
