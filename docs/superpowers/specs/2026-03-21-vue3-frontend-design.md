# Vue3 Web 前端设计文档

**日期**: 2026-03-21
**主题**: AI 聊天 Web 前端页面设计

---

## 1. 项目概述

### 1.1 目标

使用 Vue3 开发一个 Web 前台客户端页面，用于访问和管理 Agent 项目。首期实现 AI 聊天功能。

### 1.2 范围

本文档描述第一阶段的 AI 聊天页面设计，包括：
- 聊天对话界面
- 会话管理功能
- 与后端 API 的集成

---

## 2. 设计决策汇总

| 设计项 | 选择 | 说明 |
|--------|------|------|
| 整体布局 | 左右分栏 | 左侧会话管理，右侧对话区域 |
| 会话管理 | 侧边栏列表 | 点击切换，支持新建/删除 |
| 侧边栏行为 | 固定式 | 始终显示，占据 200-240px 宽度 |
| 对话气泡 | 现代风格 | 圆角气泡，左 AI/右 用户 |
| 配色方案 | 蓝色主题 | 主色 #3B82F6，专业科技感 |
| 输入方式 | 多行文本域 | 可调整高度，Shift+Enter 换行 |
| 会话 ID | 前端生成 | 简化后端接口 |

---

## 3. 架构设计

### 3.1 前端技术栈

```
Vue 3 (Composition API)
├── Vite (构建工具)
├── TypeScript (类型安全)
├── Pinia (状态管理)
├── Vue Router (路由)
└── Tailwind CSS (样式)
```

### 3.2 目录结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatArea.vue       # 对话区域
│   │   ├── MessageBubble.vue  # 消息气泡
│   │   ├── Sidebar.vue        # 侧边栏
│   │   └── InputArea.vue      # 输入区域
│   ├── composables/
│   │   ├── useChat.ts         # 聊天逻辑
│   │   └── useSessions.ts     # 会话管理
│   ├── stores/
│   │   ├── chatStore.ts       # 聊天状态
│   │   └── sessionStore.ts    # 会话状态
│   ├── types/
│   │   └── index.ts           # TypeScript 类型
│   ├── api/
│   │   └── client.ts          # API 客户端
│   ├── App.vue
│   └── main.ts
├── package.json
└── vite.config.ts
```

### 3.3 后端 API 设计

#### 3.3.1 现有接口

```
POST /api/v1/chat
Request:
{
  "user_id": string,
  "channel_id": string,
  "message": string
}

Response:
{
  "session_id": string,
  "reply": string,
  "agent_name": string
}
```

#### 3.3.2 新增接口（Web Controller）

```
GET /api/v1/web/sessions
Response:
{
  "sessions": [
    {"session_id": string, "created_at": string, "updated_at": string}
  ]
}

POST /api/v1/web/sessions
Request: { "user_id": string }
Response: { "session_id": string }

DELETE /api/v1/web/sessions/:session_id
Response: { "success": boolean }
```

---

## 4. 组件设计

### 4.1 主布局组件

```
┌─────────────────────────────────────────────┐
│  Header (可选)                               │
├──────────────┬──────────────────────────────┤
│              │                              │
│   Sidebar    │        ChatArea              │
│  (固定 200px) │      (flex-1)               │
│              │                              │
│  - 会话列表   │   - 消息列表                 │
│  - 新建按钮   │   - 输入框                   │
│              │                              │
└──────────────┴──────────────────────────────┘
```

### 4.2 状态管理

**SessionStore**:
- `sessions`: 会话列表
- `currentSessionId`: 当前会话 ID
- `createSession()`: 创建新会话
- `deleteSession(id)`: 删除会话
- `selectSession(id)`: 切换会话

**ChatStore**:
- `messages`: 当前会话消息列表
- `isLoading`: 加载状态
- `sendMessage(content)`: 发送消息
- `clearMessages()`: 清空消息

### 4.3 数据流

```
用户输入 → InputArea → useChat.sendMessage()
                    → API /api/v1/chat
                    → ChatStore.messages.push()
                    → MessageBubble 渲染

侧边栏点击 → Sidebar → useSessions.selectSession()
                    → ChatStore.clearMessages()
                    → 加载历史消息
```

---

## 5. 样式设计

### 5.1 颜色变量

```css
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
```

### 5.2 消息气泡样式

```css
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

---

## 6. 会话管理

### 6.1 Session ID 生成

前端使用 UUID v4 生成 session_id：
```typescript
const generateSessionId = () => {
  return `${userId}_${crypto.randomUUID()}`;
};
```

### 6.2 本地持久化

使用 localStorage 存储当前会话 ID：
```typescript
localStorage.setItem('currentSessionId', sessionId);
```

### 6.3 会话列表

由于后端使用内存存储，会话列表通过本地历史记录实现：
- 每次创建新会话时记录到 localStorage
- 显示最近 N 个会话
- 点击加载对应会话历史

---

## 7. 错误处理

### 7.1 网络错误

- 请求超时提示"网络连接超时，请重试"
- 自动重试机制（最多 3 次）

### 7.2 后端错误

- 400: 显示"请求参数错误"
- 500: 显示"服务器错误，请稍后重试"
- 未知错误：显示错误详情

---

## 8. 测试计划

### 8.1 单元测试

- 组件渲染测试
- 状态管理测试
- API 调用 mock 测试

### 8.2 集成测试

- 完整聊天流程
- 会话切换流程
- 错误处理流程

---

## 9. 验收标准

- [ ] 页面布局符合设计（左右分栏，固定侧边栏）
- [ ] 消息气泡样式正确（圆角，左右区分）
- [ ] 会话管理功能正常（新建/切换/删除）
- [ ] 输入框支持多行输入和 Shift+Enter
- [ ] 与后端 API 集成成功
- [ ] 响应式布局（适配主流屏幕尺寸）
- [ ] 错误处理完善

---

## 10. 后续扩展

### 10.1 第二阶段功能

- Markdown 渲染支持
- 代码高亮显示
- 消息编辑/删除
- 会话重命名

### 10.2 第三阶段功能

- Agent 切换选择器
- 对话历史搜索
- 导出对话记录
- 主题切换（深色模式）
