import { db } from '../db/client.js'

export const list = () => db.flow.findMany({ orderBy: { createdAt: 'desc' } })
export const create = ({ name }: { name: string }) => db.flow.create({ data: { name } })
export const byId = (id: string) => db.flow.findUnique({ where: { id } })
export const remove = async (id: string) => {
  const f = await db.flow.findUnique({ where: { id } })
  if (!f) return false
  await db.flow.delete({ where: { id } })
  return true
}

export async function newOrActiveThread(flowId: string) {
  const last = await db.thread.findFirst({
    where: { flowId, archived: false, status: { in: ['NEW','IN_PROGRESS'] } },
    orderBy: { startedAt: 'desc' }
  })
  if (last) return last
  return db.thread.create({ data: { flowId, status: 'NEW' } })
}
