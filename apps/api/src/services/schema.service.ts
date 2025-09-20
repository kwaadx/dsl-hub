import { db } from '../db/client.js'
export const register = ({ name = 'DSL', version = '3.0', json = {} }: any) => db.schemaDef.create({ data: { name, version, json } })
export const list = () => db.schemaDef.findMany({ orderBy: [{ name: 'asc' }, { version: 'desc' }] })
