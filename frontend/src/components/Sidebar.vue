<script setup lang="ts">
import { useSessionStore } from '@/stores/sessionStore'

const sessionStore = useSessionStore()

const emit = defineEmits<{
  (e: 'create'): void
  (e: 'select', sessionId: string): void
  (e: 'delete', sessionId: string): void
}>()

function handleCreate() {
  emit('create')
}

function handleSelect(sessionId: string) {
  emit('select', sessionId)
}

function handleDelete(sessionId: string) {
  emit('delete', sessionId)
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2 class="sidebar-title">💬 会话</h2>
      <button class="new-btn" @click="handleCreate">+ 新建</button>
    </div>
    <div class="session-list">
      <div
        v-for="sessionId in sessionStore.sessions"
        :key="sessionId"
        class="session-item"
        :class="{ active: sessionId === sessionStore.currentSessionId }"
        @click="handleSelect(sessionId)"
      >
        <span class="session-name">{{ sessionId.slice(0, 20) }}...</span>
        <button class="delete-btn" @click.stop="handleDelete(sessionId)">×</button>
      </div>
      <div v-if="sessionStore.sessions.length === 0" class="empty-message">
        暂无会话，点击"+新建"开始
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 220px;
  height: 100%;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border);
}

.sidebar-title {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0;
}

.new-btn {
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 0.75rem;
  cursor: pointer;
}

.new-btn:hover {
  background: var(--primary-hover);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.session-list::-webkit-scrollbar {
  width: 6px;
}

.session-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  margin: 4px 0;
  cursor: pointer;
  font-size: 0.85rem;
}

.session-item:hover {
  background: #e2e8f0;
}

.session-item.active {
  background: #dbeafe;
  color: var(--primary);
}

.session-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1rem;
  padding: 0 4px;
}

.delete-btn:hover {
  color: #ef4444;
}

.empty-message {
  text-align: center;
  color: #94a3b8;
  font-size: 0.75rem;
  padding: 1rem 0.5rem;
}
</style>
