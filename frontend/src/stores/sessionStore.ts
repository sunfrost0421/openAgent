import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'agent_sessions'
const CURRENT_KEY = 'agent_current_session'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref<string[]>([])
  const currentSessionId = ref<string>('')

  const currentSession = computed(() => currentSessionId.value || null)

  function generateSessionId(userId: string): string {
    const uuid = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2)
    return `${userId}_${uuid}`
  }

  function createSession(userId: string): string {
    const sessionId = generateSessionId(userId)
    sessions.value.unshift(sessionId)
    currentSessionId.value = sessionId
    persistSessions()
    return sessionId
  }

  function selectSession(sessionId: string): void {
    currentSessionId.value = sessionId
    localStorage.setItem(CURRENT_KEY, sessionId)
  }

  function deleteSession(sessionId: string): void {
    sessions.value = sessions.value.filter(id => id !== sessionId)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = sessions.value[0] || ''
    }
    persistSessions()
  }

  function loadSessions(): void {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      sessions.value = JSON.parse(stored)
    }
    const current = localStorage.getItem(CURRENT_KEY)
    if (current) {
      currentSessionId.value = current
    }
  }

  function persistSessions(): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.value))
    if (currentSessionId.value) {
      localStorage.setItem(CURRENT_KEY, currentSessionId.value)
    }
  }

  return {
    sessions,
    currentSessionId,
    currentSession,
    createSession,
    selectSession,
    deleteSession,
    loadSessions,
  }
})
