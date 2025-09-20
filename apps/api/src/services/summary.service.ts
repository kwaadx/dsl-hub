import { db } from '../db/client.js'
export const getGlobal = async () => (await db.globalSummary.findFirst()) ?? (await db.globalSummary.create({ data: { content: {} } }))
export const upsertGlobal = async (content: any) => {
  const g = await db.globalSummary.findFirst()
  if (!g) return db.globalSummary.create({ data: { content } })
  return db.globalSummary.update({ where: { id: g.id }, data: { content } })
}
export const flowLatest = (flowId: string) => db.flowSummary.findFirst({ where: { flowId }, orderBy: { updatedAt: 'desc' } })
export const flowCreate = (flowId: string, content: any) => db.flowSummary.create({ data: { flowId, content } })
