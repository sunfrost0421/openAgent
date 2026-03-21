import { useChatStore } from '@/stores/chatStore'
import { useSessionStore } from '@/stores/sessionStore'
import { chatApi } from '@/api/client'

const DEFAULT_USER_ID = 'web_user'

export function useChat() {
  const chatStore = useChatStore()
  const sessionStore = useSessionStore()

  async function sendMessage(content: string): Promise<void> {
    if (!content.trim() || !sessionStore.currentSessionId) return

    chatStore.addUserMessage(content)
    chatStore.setLoading(true)

    try {
      const response = await chatApi.sendMessage({
        user_id: DEFAULT_USER_ID,
        channel_id: sessionStore.currentSessionId,
        message: content,
      })

      chatStore.addAIMessage(response.reply, response.agent_name)
    } catch (error) {
      chatStore.addAIMessage('抱歉，发生了错误：' + (error as Error).message)
    } finally {
      chatStore.setLoading(false)
    }
  }

  function switchSession(sessionId: string): void {
    sessionStore.selectSession(sessionId)
    chatStore.clearMessages()
  }

  return {
    messages: chatStore.messages,
    isLoading: chatStore.isLoading,
    sendMessage,
    switchSession,
  }
}
