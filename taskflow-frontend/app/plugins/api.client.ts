export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()
  const apiBase = String(config.public.apiBase).replace(/\/+$/, '')

  const api = $fetch.create({
    baseURL: apiBase,
    credentials: 'include',
    onRequest({ options }) {
      const method = String(options.method ?? 'GET').toUpperCase()
      if (['GET', 'HEAD', 'OPTIONS'].includes(method)) return

      const csrfCookie = document.cookie
        .split('; ')
        .find((cookie) => cookie.startsWith('taskflow_csrf='))
        ?.slice('taskflow_csrf='.length)
      if (!csrfCookie) return

      const headers = new Headers(options.headers)
      headers.set('X-CSRF-Token', decodeURIComponent(csrfCookie))
      options.headers = headers
    },
  })

  return {
    provide: { api },
  }
})
