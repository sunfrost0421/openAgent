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
