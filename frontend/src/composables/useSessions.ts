import { useSessionStore } from '@/stores/sessionStore'
import api from '@/api/client'

export function useSessions() {
  const sessionStore = useSessionStore()

  async function createNewSession(userId: string): Promise<string> {
    try {
      const response = await api.post('/web/sessions', { user_id: userId })
      const sessionId = response.data.session_id
      sessionStore.createSession(userId)
      return sessionId
    } catch (error) {
      // API 不存在时，只在本地创建会话
      return sessionStore.createSession(userId)
    }
  }

  async function deleteSession(sessionId: string): Promise<void> {
    try {
      await api.delete(`/web/sessions/${sessionId}`)
    } catch (error) {
      // API 不存在时，只在本地删除
    }
    sessionStore.deleteSession(sessionId)
  }

  function selectSession(sessionId: string): void {
    sessionStore.selectSession(sessionId)
  }

  return {
    sessions: sessionStore.sessions,
    currentSessionId: sessionStore.currentSessionId,
    createNewSession,
    deleteSession,
    selectSession,
  }
}
