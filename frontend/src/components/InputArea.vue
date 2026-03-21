<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'send', content: string): void
}>()

defineProps<{
  disabled?: boolean
}>()

const inputValue = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function handleSend() {
  const content = inputValue.value.trim()
  if (!content) return
  emit('send', content)
  inputValue.value = ''
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
}

function adjustHeight() {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = textareaRef.value.scrollHeight + 'px'
  }
}
</script>

<template>
  <div class="input-area">
    <textarea
      ref="textareaRef"
      v-model="inputValue"
      class="textarea"
      placeholder="输入消息...（Shift+Enter 换行）"
      :disabled="disabled"
      @keydown="handleKeydown"
      @input="adjustHeight"
      rows="1"
    />
    <div class="input-footer">
      <span class="hint">支持 Markdown 语法</span>
      <button class="send-btn" @click="handleSend" :disabled="disabled || !inputValue.trim()">
        发送
      </button>
    </div>
  </div>
</template>

<style scoped>
.input-area {
  border-top: 1px solid var(--border);
  padding: 1rem;
  background: white;
}

.textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.9rem;
  resize: none;
  min-height: 40px;
  max-height: 200px;
  font-family: inherit;
  background: white;
  box-sizing: border-box;
}

.textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.textarea:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.hint {
  font-size: 0.75rem;
  color: #64748b;
}

.send-btn {
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 20px;
  font-size: 0.9rem;
  cursor: pointer;
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.send-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
</style>
