export function getHttpStatus(error: any): number | undefined {
  return error?.status ?? error?.response?.status ?? error?.cause?.status
}

export function retry404Safe(failureCount: number, error: any, maxAttempts = 2): boolean {
  const status = getHttpStatus(error)
  if (status === 404) return false
  return failureCount < maxAttempts
}
