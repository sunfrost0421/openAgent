import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Message } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const isLoading = ref(false)

  function addUserMessage(content: string): void {
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'user',
      content,
      createdAt: new Date(),
    })
  }

  function addAIMessage(content: string, agentName?: string): void {
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'ai',
      content,
      agentName,
      createdAt: new Date(),
    })
  }

  function clearMessages(): void {
    messages.value = []
  }

  function setLoading(loading: boolean): void {
    isLoading.value = loading
  }

  return {
    messages,
    isLoading,
    addUserMessage,
    addAIMessage,
    clearMessages,
    setLoading,
  }
})
