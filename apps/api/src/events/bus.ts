import EE from 'eventemitter3'
export const bus = new EE<{
  'agent:token': (p: { threadId: string; token: string }) => void
  'agent:done': (p: { threadId: string; summary?: any; success?: boolean }) => void
}>()
