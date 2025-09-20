import type { RequestHandler } from 'express'
import type { ZodSchema } from 'zod'
export const validate = (schema: ZodSchema): RequestHandler => (req, _res, next) => {
  const r = schema.safeParse({ body: (req as any).body, params: req.params, query: req.query })
  if (!r.success) return next({ status: 400, message: r.error.issues.map(i => i.message).join('; ') })
  Object.assign(req, r.data)
  next()
}
