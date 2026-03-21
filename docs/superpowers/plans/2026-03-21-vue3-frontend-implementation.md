# Vue3 Web 前端实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用 Vue3 + TypeScript + Pinia + Tailwind CSS 开发 AI 聊天 Web 前端，实现左右分栏布局、会话管理和聊天对话功能。

**Architecture:**
- 前端：Vue3 单页应用，Vite 构建，Pinia 状态管理，Tailwind CSS 样式
- 后端：FastAPI 现有 `/api/v1/chat` 接口，新增 `/api/v1/web/sessions` 会话管理接口
- 会话 ID：前端生成 UUID，通过 localStorage 持久化
- 布局：固定侧边栏（220px）+ 弹性对话区域

**Tech Stack:** Vue 3.4+, TypeScript 5.x, Vite 5.x, Pinia 2.x, Vue Router 4.x, Tailwind CSS 3.x, Axios 1.x

---

## Chunk 1: 项目初始化和配置

### Task 1: 创建 Vue3 项目骨架

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "agent-web-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.7",
    "uuid": "^9.0.1"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.4",
    "vite": "^5.1.4",
    "typescript": "^5.3.3",
    "vue-tsc": "^2.0.6",
    "tailwindcss": "^3.4.1",
    "postcss": "^8.4.35",
    "autoprefixer": "^10.4.17",
    "vitest": "^1.3.1",
    "@vue/test-utils": "^2.4.4",
    "eslint": "^8.57.0",
    "eslint-plugin-vue": "^9.22.0",
    "@types/uuid": "^9.0.8"
  }
}
```

- [ ] **Step 2: 创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'happy-dom',
  },
})
```

- [ ] **Step 3: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 4: 创建 tsconfig.node.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts", "vitest.config.ts"]
}
```

- [ ] **Step 5: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Agent Chat</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 6: 创建 gitignore**

```
node_modules
dist
.DS_Store
*.local
.env
```

- [ ] **Step 7: 提交**

```bash
cd frontend
git add package.json vite.config.ts tsconfig.json tsconfig.node.json index.html .gitignore
git commit -m "chore: initialize Vue3 project with Vite and TypeScript"
```

---

### Task 2: 配置 Tailwind CSS 和样式系统

**Files:**
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/styles/main.css`

- [ ] **Step 1: 创建 tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
        },
        user: {
          bg: '#dbeafe',
          text: '#1e40af',
        },
        ai: {
          bg: '#f1f5f9',
          text: '#1e293b',
        },
        sidebar: {
          bg: '#f8fafc',
        },
      },
      maxWidth: {
        'chat-bubble': '70%',
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 2: 创建 postcss.config.js**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 3: 创建 src/styles/main.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --primary: #3b82f6;
  --primary-hover: #2563eb;
  --user-bg: #dbeafe;
  --user-text: #1e40af;
  --ai-bg: #f1f5f9;
  --ai-text: #1e293b;
  --sidebar-bg: #f8fafc;
  --border: #e2e8f0;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

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
```

- [ ] **Step 4: 提交**

```bash
cd frontend
git add tailwind.config.js postcss.config.js src/styles/main.css
git commit -m "chore: configure Tailwind CSS with custom theme"
```

---

### Task 3: 创建基础目录结构和入口文件

**Files:**
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/stores/index.ts`
- Create: `frontend/src/composables/index.ts`

- [ ] **Step 1: 创建 src/types/index.ts**

```typescript
export interface Message {
  id: string
  role: 'user' | 'ai'
  content: string
  agentName?: string
  createdAt: Date
}

export interface Session {
  sessionId: string
  createdAt: string
  updatedAt: string
}

export interface ChatRequest {
  user_id: string
  channel_id: string
  message: string
}

export interface ChatResponse {
  session_id: string
  reply: string
  agent_name: string
}

export interface SessionsListResponse {
  sessions: Session[]
}

export interface CreateSessionRequest {
  user_id: string
}

export interface CreateSessionResponse {
  session_id: string
}
```

- [ ] **Step 2: 创建 src/api/client.ts**

```typescript
import axios from 'axios'
import type { ChatRequest, ChatResponse, CreateSessionResponse } from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

export const chatApi = {
  async sendMessage(data: ChatRequest): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/chat', data)
    return response.data
  },

  async createSession(userId: string): Promise<string> {
    const response = await api.post<CreateSessionResponse>('/web/sessions', { user_id: userId })
    return response.data.session_id
  },
}

export default api
```

- [ ] **Step 3: 创建 src/main.ts**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './styles/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')
```

- [ ] **Step 4: 创建 src/stores/index.ts**（空导出，后续任务实现）

```typescript
// Store exports will be added in subsequent tasks
export {}
```

- [ ] **Step 5: 创建 src/composables/index.ts**（空导出，后续任务实现）

```typescript
// Composable exports will be added in subsequent tasks
export {}
```

- [ ] **Step 6: 创建 src/App.vue**

```vue
<script setup lang="ts">
// Root component - layout will be added in subsequent tasks
</script>

<template>
  <div id="app" class="h-screen w-screen">
    <!-- Main layout will be added -->
  </div>
</template>

<style scoped>
#app {
  height: 100%;
  width: 100%;
}
</style>
```

- [ ] **Step 7: 提交**

```bash
cd frontend
git add src/main.ts src/App.vue src/types/index.ts src/api/client.ts src/stores/index.ts src/composables/index.ts src/styles/main.css
git commit -m "feat: create base project structure with types and API client"
```

---

## Chunk 2: 状态管理

### Task 4: 实现 SessionStore

**Files:**
- Modify: `frontend/src/stores/index.ts`
- Create: `frontend/src/stores/sessionStore.ts`
- Test: `frontend/src/stores/__tests__/sessionStore.test.ts`

- [ ] **Step 1: 编写测试**

```typescript
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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd frontend
npm run test -- src/stores/__tests__/sessionStore.test.ts
```
Expected: FAIL with "sessionStore not found"

- [ ] **Step 3: 实现 SessionStore**

```typescript
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
```

- [ ] **Step 4: 更新 stores/index.ts**

```typescript
export { useSessionStore } from './sessionStore'
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd frontend
npm run test -- src/stores/__tests__/sessionStore.test.ts
```
Expected: PASS

- [ ] **Step 6: 提交**

```bash
cd frontend
git add src/stores/sessionStore.ts src/stores/index.ts src/stores/__tests__/sessionStore.test.ts
git commit -m "feat: implement session store with localStorage persistence"
```

---

### Task 5: 实现 ChatStore

**Files:**
- Create: `frontend/src/stores/chatStore.ts`
- Test: `frontend/src/stores/__tests__/chatStore.test.ts`

- [ ] **Step 1: 编写测试**

```typescript
import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, beforeEach } from 'vitest'
import { useChatStore } from '../chatStore'
import type { Message } from '@/types'

describe('chatStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('adds a user message', () => {
    const store = useChatStore()
    store.addUserMessage('Hello')
    expect(store.messages).toHaveLength(1)
    expect(store.messages[0].role).toBe('user')
    expect(store.messages[0].content).toBe('Hello')
  })

  it('adds an AI message', () => {
    const store = useChatStore()
    store.addAIMessage('Hi there', 'default_agent')
    expect(store.messages).toHaveLength(1)
    expect(store.messages[0].role).toBe('ai')
    expect(store.messages[0].agentName).toBe('default_agent')
  })

  it('clears messages', () => {
    const store = useChatStore()
    store.addUserMessage('Hello')
    store.addAIMessage('Hi')
    store.clearMessages()
    expect(store.messages).toHaveLength(0)
  })

  it('sets loading state', () => {
    const store = useChatStore()
    store.setLoading(true)
    expect(store.isLoading).toBe(true)
    store.setLoading(false)
    expect(store.isLoading).toBe(false)
  })
})
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd frontend
npm run test -- src/stores/__tests__/chatStore.test.ts
```
Expected: FAIL

- [ ] **Step 3: 实现 ChatStore**

```typescript
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
```

- [ ] **Step 4: 更新 stores/index.ts**

```typescript
export { useSessionStore } from './sessionStore'
export { useChatStore } from './chatStore'
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd frontend
npm run test -- src/stores/__tests__/chatStore.test.ts
```
Expected: PASS

- [ ] **Step 6: 提交**

```bash
cd frontend
git add src/stores/chatStore.ts src/stores/index.ts src/stores/__tests__/chatStore.test.ts
git commit -m "feat: implement chat store for message management"
```

---

## Chunk 3: 组件开发

### Task 6: 实现 Sidebar 组件

**Files:**
- Create: `frontend/src/components/Sidebar.vue`
- Create: `frontend/src/composables/useSessions.ts`
- Test: `frontend/src/components/__tests__/Sidebar.test.ts`

- [ ] **Step 1: 实现 useSessions composable**

```typescript
import { useSessionStore } from '@/stores/sessionStore'
import { api } from '@/api/client'

export function useSessions() {
  const sessionStore = useSessionStore()

  async function createNewSession(userId: string): Promise<string> {
    const response = await api.post('/web/sessions', { user_id: userId })
    const sessionId = response.data.session_id
    sessionStore.createSession(userId)
    return sessionId
  }

  async function deleteSession(sessionId: string): Promise<void> {
    await api.delete(`/web/sessions/${sessionId}`)
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
```

- [ ] **Step 2: 实现 Sidebar 组件**

```vue
<script setup lang="ts">
import { computed } from 'vue'
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

function handleDelete(sessionId: string, event: Event) {
  event.stopPropagation()
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
        <button class="delete-btn" @click="handleDelete(sessionId)">×</button>
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
</style>
```

- [ ] **Step 3: 提交**

```bash
cd frontend
git add src/composables/useSessions.ts src/components/Sidebar.vue
git commit -m "feat: implement Sidebar component with session management"
```

---

### Task 7: 实现 MessageBubble 组件

**Files:**
- Create: `frontend/src/components/MessageBubble.vue`
- Test: `frontend/src/components/__tests__/MessageBubble.test.ts`

- [ ] **Step 1: 编写测试**

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageBubble from '../MessageBubble.vue'

describe('MessageBubble', () => {
  it('renders user message with correct class', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        message: {
          id: '1',
          role: 'user',
          content: 'Hello',
          createdAt: new Date(),
        },
      },
    })
    expect(wrapper.classes()).toContain('message')
    expect(wrapper.classes()).toContain('user')
  })

  it('renders AI message with correct class', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        message: {
          id: '1',
          role: 'ai',
          content: 'Hi',
          createdAt: new Date(),
        },
      },
    })
    expect(wrapper.classes()).toContain('message')
    expect(wrapper.classes()).toContain('ai')
  })

  it('displays message content', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        message: {
          id: '1',
          role: 'user',
          content: 'Test message',
          createdAt: new Date(),
        },
      },
    })
    expect(wrapper.text()).toContain('Test message')
  })
})
```

- [ ] **Step 2: 实现 MessageBubble 组件**

```vue
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
```

- [ ] **Step 3: 提交**

```bash
cd frontend
git add src/components/MessageBubble.vue src/components/__tests__/MessageBubble.test.ts
git commit -m "feat: implement MessageBubble component"
```

---

### Task 8: 实现 ChatArea 组件

**Files:**
- Create: `frontend/src/components/ChatArea.vue`
- Create: `frontend/src/composables/useChat.ts`

- [ ] **Step 1: 实现 useChat composable**

```typescript
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
```

- [ ] **Step 2: 实现 ChatArea 组件**

```vue
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
```

- [ ] **Step 3: 提交**

```bash
cd frontend
git add src/components/ChatArea.vue src/composables/useChat.ts
git commit -m "feat: implement ChatArea component"
```

---

### Task 9: 实现 InputArea 组件

**Files:**
- Create: `frontend/src/components/InputArea.vue`
- Test: `frontend/src/components/__tests__/InputArea.test.ts`

- [ ] **Step 1: 编写测试**

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import InputArea from '../InputArea.vue'

describe('InputArea', () => {
  it('renders textarea and send button', () => {
    const wrapper = mount(InputArea)
    expect(wrapper.find('textarea').exists()).toBe(true)
    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('emits send event when button clicked', async () => {
    const wrapper = mount(InputArea)
    const textarea = wrapper.find('textarea')
    await textarea.setValue('Hello')
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('send')).toBeTruthy()
    expect(wrapper.emitted('send')?.[0]).toEqual(['Hello'])
  })

  it('emits send event on Enter without Shift', async () => {
    const wrapper = mount(InputArea)
    const textarea = wrapper.find('textarea')
    await textarea.setValue('Hello')
    await textarea.trigger('keydown', { key: 'Enter', shiftKey: false })
    expect(wrapper.emitted('send')).toBeTruthy()
  })

  it('does not emit on Shift+Enter', async () => {
    const wrapper = mount(InputArea)
    const textarea = wrapper.find('textarea')
    await textarea.trigger('keydown', { key: 'Enter', shiftKey: true })
    expect(wrapper.emitted('send')).toBeFalsy()
  })

  it('disables when disabled prop is true', () => {
    const wrapper = mount(InputArea, { props: { disabled: true } })
    expect(wrapper.find('textarea').element.disabled).toBe(true)
  })
})
```

- [ ] **Step 2: 实现 InputArea 组件**

```vue
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
```

- [ ] **Step 3: 提交**

```bash
cd frontend
git add src/components/InputArea.vue src/components/__tests__/InputArea.test.ts
git commit -m "feat: implement InputArea component with multi-line support"
```

---

### Task 10: 实现主布局并组装所有组件

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 更新 App.vue**

```vue
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
```

- [ ] **Step 2: 提交**

```bash
cd frontend
git add src/App.vue
git commit -m "feat: assemble main layout with all components"
```

---

## Chunk 4: 后端 API 集成

### Task 11: 创建后端 Web Controller

**Files:**
- Create: `D:\workplace\qrc\new3\src\controller\web_controller.py`
- Modify: `D:\workplace\qrc\new3\main.py`

- [ ] **Step 1: 创建 web_controller.py**

```python
"""Web Controller - 前端 API 接口"""

import logging
from typing import List, Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.session.manager import session_manager

router = APIRouter()
_logger = logging.getLogger("WebController")


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    created_at: str
    updated_at: str


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    user_id: str


class CreateSessionResponse(BaseModel):
    """创建会话响应"""
    session_id: str


@router.get("/sessions", response_model=Dict[str, List[SessionInfo]])
async def list_sessions() -> Dict[str, List[SessionInfo]]:
    """获取会话列表"""
    # 当前实现返回空列表，实际使用时从存储中获取
    return {"sessions": []}


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
    """创建新会话"""
    # 前端生成 session_id，后端只需确认
    return CreateSessionResponse(session_id=f"{request.user_id}_{datetime.now().isoformat()}")


@router.delete("/sessions/{session_id}", response_model=Dict[str, bool])
async def delete_session(session_id: str) -> Dict[str, bool]:
    """删除会话"""
    # 当前实现直接返回成功
    return {"success": True}
```

- [ ] **Step 2: 更新 main.py 注册路由**

```python
from src.controller.web_controller import router as web_router

# 在现有的 include_router 后添加
app.include_router(router, prefix="/api/v1")
app.include_router(web_router, prefix="/api/v1/web")
```

- [ ] **Step 3: 测试后端启动**

```bash
cd D:\workplace\qrc\new3
python main.py
```
Expected: Server starts successfully at http://localhost:8000

- [ ] **Step 4: 测试 API 端点**

```bash
curl http://localhost:8000/api/v1/web/sessions
```
Expected: `{"sessions": []}`

- [ ] **Step 5: 提交**

```bash
cd D:\workplace\qrc\new3
git add src/controller/web_controller.py main.py
git commit -m "feat: add web controller for frontend API"
```

---

## Chunk 5: 测试和验收

### Task 12: 端到端测试

**Files:**
- Create: `frontend/tests/e2e/chat.test.ts`

- [ ] **Step 1: 配置 Vitest 集成测试**

```bash
cd frontend
npm install -D @vitest/ui jsdom
```

- [ ] **Step 2: 创建集成测试**

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from '../../src/App.vue'

describe('E2E Chat Flow', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders the main layout', () => {
    const app = createApp(App)
    app.use(createPinia())
    const container = document.createElement('div')
    app.mount(container)

    expect(container.querySelector('.sidebar')).toBeTruthy()
    expect(container.querySelector('.chat-area')).toBeTruthy()
  })

  it('creates a new session on mount', () => {
    const app = createApp(App)
    app.use(createPinia())
    const container = document.createElement('div')
    app.mount(container)

    const storedSessions = localStorage.getItem('agent_sessions')
    expect(storedSessions).toBeTruthy()
  })
})
```

- [ ] **Step 3: 运行测试**

```bash
cd frontend
npm run test
```
Expected: All tests pass

- [ ] **Step 4: 提交**

```bash
cd frontend
git add tests/e2e/chat.test.ts
git commit -m "test: add e2e integration tests"
```

---

### Task 13: 手动验收测试

**Files:**
- Create: `frontend/ACCEPTANCE.md`

- [ ] **Step 1: 创建验收文档**

```markdown
# 验收标准检查清单

## 功能验收

- [ ] 页面布局：左右分栏，侧边栏固定 220px
- [ ] 侧边栏显示会话列表
- [ ] 点击"+新建"创建新会话
- [ ] 点击会话项切换会话
- [ ] 点击×删除会话
- [ ] 输入消息并按 Enter 发送
- [ ] Shift+Enter 换行
- [ ] 消息气泡正确显示（左 AI/右 用户）
- [ ] 蓝色主题配色正确
- [ ] 加载状态显示正确

## API 集成验收

- [ ] 后端服务启动在 http://localhost:8000
- [ ] 前端服务启动在 http://localhost:3000
- [ ] 发送消息成功调用 /api/v1/chat
- [ ] 收到 AI 响应并显示

## 兼容性验收

- [ ] Chrome 浏览器正常工作
- [ ] Edge 浏览器正常工作
- [ ] Firefox 浏览器正常工作
- [ ] 响应式布局在 1920x1080 正常
- [ ] 响应式布局在 1366x768 正常
```

- [ ] **Step 2: 启动前端并测试**

```bash
cd frontend
npm run dev
```

- [ ] **Step 3: 启动后端并测试**

```bash
cd D:\workplace\qrc\new3
python main.py
```

- [ ] **Step 4: 提交**

```bash
cd frontend
git add ACCEPTANCE.md
git commit -m "docs: add acceptance test checklist"
```

---

## 完成

执行以下命令确认所有任务完成：

```bash
cd frontend
npm run build
```

Expected: Build succeeds with no errors

```bash
cd D:\workplace\qrc\new3
git status
```

Expected: Working tree clean

---

**计划完成！准备执行？**
