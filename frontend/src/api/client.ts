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
