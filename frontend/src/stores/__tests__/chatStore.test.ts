import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, beforeEach } from 'vitest'
import { useChatStore } from '../chatStore'

describe('chatStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('adds a user message', () => {
    const store = useChatStore()
    store.addUserMessage('Hello')
    expect(store.messages).toHaveLength(1)
    expect(store.messages[0].role).toBe('user')
    expect(store.messages[0].content).toBe('Hello')
  })

  it('adds an AI message', () => {
    const store = useChatStore()
    store.addAIMessage('Hi there', 'default_agent')
    expect(store.messages).toHaveLength(1)
    expect(store.messages[0].role).toBe('ai')
    expect(store.messages[0].agentName).toBe('default_agent')
  })

  it('clears messages', () => {
    const store = useChatStore()
    store.addUserMessage('Hello')
    store.addAIMessage('Hi')
    store.clearMessages()
    expect(store.messages).toHaveLength(0)
  })

  it('sets loading state', () => {
    const store = useChatStore()
    store.setLoading(true)
    expect(store.isLoading).toBe(true)
    store.setLoading(false)
    expect(store.isLoading).toBe(false)
  })
})
