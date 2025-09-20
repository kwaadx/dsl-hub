// Placeholder: ChatGPT-5 client (to be swapped for real SDK).
export async function chat(prompt: string): Promise<AsyncGenerator<string>> {
  async function* gen() {
    for (const t of ['This',' ','is',' ','streamed',' ','text','.']) { yield t; await new Promise(r=>setTimeout(r,90)) }
  }
  return gen()
}
