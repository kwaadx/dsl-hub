import { db } from '../db/client.js'
export const write = ({ flowId, threadId, level = 'info', event = 'note', data = {} }: any) =>
  db.agentLog.create({ data: { flowId, threadId, level, event, data } })
