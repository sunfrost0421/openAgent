<script setup lang="ts">
import { ref, watch } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import MessageBubble from './MessageBubble.vue'
import InputArea from './InputArea.vue'

const chatStore = useChatStore()

const emit = defineEmits<{
  (e: 'send', content: string): Promise<void>
}>()

const messagesEnd = ref<HTMLElement | null>(null)

function scrollToBottom() {
  messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
}

watch(() => chatStore.messages, scrollToBottom, { deep: true })
</script>

<template>
  <main class="chat-area">
    <div class="messages-container">
      <MessageBubble
        v-for="message in chatStore.messages"
        :key="message.id"
        :message="message"
      />
      <div ref="messagesEnd" />
    </div>
    <InputArea @send="emit('send', $event)" :disabled="chatStore.isLoading" />
  </main>
</template>

<style scoped>
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
</style>
