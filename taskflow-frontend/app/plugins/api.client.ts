export default defineNuxtPlugin(() => {
  // Centraliza a base da API para que páginas usem caminhos relativos.
  const config = useRuntimeConfig()
  const apiBase = String(config.public.apiBase).replace(/\/+$/, '')

  // Anexa o token apenas aos pedidos da API, sem o guardar em cookies partilhados.
  const api = $fetch.create({
    baseURL: apiBase,
    onRequest({ options }) {
      const token = sessionStorage.getItem('taskflow-access-token')
      if (!token) return

      const headers = new Headers(options.headers)
      headers.set('Authorization', `Bearer ${token}`)
      options.headers = headers
    },
  })

  return {
    provide: { api },
  }
})
