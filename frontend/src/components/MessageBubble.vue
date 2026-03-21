<script setup lang="ts">
import type { Message } from '@/types'
import { computed } from 'vue'

const props = defineProps<{
  message: Message
}>()

const formattedTime = computed(() => {
  return new Date(props.message.createdAt).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
})
</script>

<template>
  <div class="message" :class="[message.role]">
    <div class="message-content">{{ message.content }}</div>
    <div class="message-time">{{ formattedTime }}</div>
  </div>
</template>

<style scoped>
.message {
  padding: 10px 14px;
  border-radius: 12px;
  margin: 8px 0;
  max-width: 70%;
  line-height: 1.4;
}

.message.user {
  background: var(--user-bg);
  color: var(--user-text);
  margin-left: auto;
}

.message.ai {
  background: var(--ai-bg);
  color: var(--ai-text);
  margin-right: auto;
}

.message-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.message-time {
  font-size: 0.7rem;
  color: #94a3b8;
  margin-top: 4px;
  text-align: right;
}

.message.ai .message-time {
  text-align: left;
}
</style>
