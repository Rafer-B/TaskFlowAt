const PAGE_SIZE = 100

export async function fetchAllPages<T>(path: string): Promise<T[]> {
  const api = useNuxtApp().$api
  const url = new URL(path, 'http://taskflow.local')
  const results: T[] = []
  let offset = 0

  while (true) {
    url.searchParams.set('limit', String(PAGE_SIZE))
    url.searchParams.set('offset', String(offset))

    const page = await api<T[]>(`${url.pathname}${url.search}`)
    results.push(...page)
    if (page.length < PAGE_SIZE) return results

    offset += PAGE_SIZE
  }
}
