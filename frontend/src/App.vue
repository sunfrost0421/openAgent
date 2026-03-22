<script setup lang="ts">
import { onMounted } from 'vue'
import { useSessionStore } from '@/stores/sessionStore'
import { useChat } from '@/composables/useChat'
import Sidebar from '@/components/Sidebar.vue'
import ChatArea from '@/components/ChatArea.vue'

const sessionStore = useSessionStore()
const { sendMessage, switchSession } = useChat()

const DEFAULT_USER_ID = 'web_user'

onMounted(() => {
  sessionStore.loadSessions()
  if (!sessionStore.currentSessionId) {
    sessionStore.createSession(DEFAULT_USER_ID)
  }
})

async function handleCreateSession() {
  const sessionId = sessionStore.createSession(DEFAULT_USER_ID)
  switchSession(sessionId)
}

async function handleDeleteSession(sessionId: string) {
  sessionStore.deleteSession(sessionId)
}

async function handleSelectSession(sessionId: string) {
  switchSession(sessionId)
}
</script>

<template>
  <div id="app" class="app-layout">
    <Sidebar
      @create="handleCreateSession"
      @select="handleSelectSession"
      @delete="handleDeleteSession"
    />
    <ChatArea @send="sendMessage" />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
</style>
