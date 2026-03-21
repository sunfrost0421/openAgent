import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, beforeEach } from 'vitest'
import { useSessionStore } from '../sessionStore'

describe('sessionStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('creates a new session', () => {
    const store = useSessionStore()
    const sessionId = store.createSession('test-user')
    expect(sessionId).toContain('test-user_')
    expect(store.currentSessionId).toBe(sessionId)
  })

  it('selects a session', () => {
    const store = useSessionStore()
    const sessionId = 'test_123'
    store.selectSession(sessionId)
    expect(store.currentSessionId).toBe(sessionId)
  })

  it('deletes a session', () => {
    const store = useSessionStore()
    const sessionId = store.createSession('test-user')
    store.deleteSession(sessionId)
    expect(store.sessions).not.toContain(sessionId)
  })

  it('loads sessions from localStorage', () => {
    localStorage.setItem('agent_sessions', JSON.stringify(['session_1', 'session_2']))
    const store = useSessionStore()
    store.loadSessions()
    expect(store.sessions).toEqual(['session_1', 'session_2'])
  })
})
