export type Role = 'user' | 'agent' | 'system'

export type MessageText = {
  id: string
  role: Role
  type: 'text'
  content: { text: string }
  ts: number
}

export type MessageActions = {
  id: string
  role: Role
  type: 'actions'
  content: {
    actions: Array<{
      id: string
      label: string
      icon?: string
      kind?: 'primary' | 'secondary' | 'danger'
      payload?: Record<string, unknown>
      event?: string // імʼя події, яке очікує бек
    }>
  }
  ts: number
}

export type MessageChoice = {
  id: string
  role: Role
  type: 'choice'
  content: {
    label: string
    kind?: 'dropdown' | 'radio'
    options: Array<{ label: string; value: string }>
  }
  ts: number
}

export type MessageCard = {
  id: string
  role: Role
  type: 'card'
  content: {
    title: string
    description?: string
    image?: string
    url?: string
    meta?: Array<{ label: string; value: string }>
  }
  ts: number
}

export type MessageNotice = {
  id: string
  role: Role
  type: 'notice'
  content: { severity?: 'info' | 'warn' | 'success' | 'error'; text: string }
  ts: number
}

export type MessageCode = {
  id: string
  role: Role
  type: 'code'
  content: { language?: string; code: string }
  ts: number
}

export type ChatMessage = MessageText | MessageActions | MessageChoice | MessageCard | MessageNotice | MessageCode
export type UserMessage = Extract<ChatMessage, { role: 'user' }>
export type AgentEvent =
  | { kind: 'action.click'; actionId: string; msgId?: string; payload?: unknown }
  | { kind: 'choice.submit'; msgId: string; payload: { value: string } }
  | { kind: 'card.open'; msgId: string; url?: string }
