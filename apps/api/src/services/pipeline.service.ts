import { db } from '../db/client.js'
export const latest = (flowId: string) => db.pipeline.findFirst({ where: { flowId }, orderBy: { createdAt: 'desc' } })
export const create = ({ flowId, version, schemaVersion, content }: { flowId: string; version: string; schemaVersion: string; content: any }) =>
  db.pipeline.create({ data: { flowId, version, schemaVersion, status: 'draft', content } })
