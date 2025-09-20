export type Button = { id: string; label: string; payload?: any }
export type Card = { title: string; subtitle?: string; body?: string; actions?: Button[] }

export type MessagePayload =
  | { format: 'text'; text: string }
  | { format: 'markdown'; md: string }
  | { format: 'json'; json: any }
  | { format: 'buttons'; buttons: Button[]; prompt?: string }
  | { format: 'card'; card: Card }
