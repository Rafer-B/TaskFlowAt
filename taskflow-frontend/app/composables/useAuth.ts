export interface AuthUser {
  id: number
  name: string
  email: string
  role: 'admin' | 'member'
  avatar_url: string | null
  is_active: boolean
  created_at: string
}

interface LoginResponse {
  access_token: string
  token_type: 'bearer'
}

export function useAuth() {
  const user = useState<AuthUser | null>('taskflow-auth-user', () => null)
  const token = useState<string>('taskflow-auth-token', () => '')
  const api = useNuxtApp().$api

  function guardarToken(value: string) {
    token.value = value
    sessionStorage.setItem('taskflow-access-token', value)
  }

  function limparSessao() {
    token.value = ''
    user.value = null
    if (import.meta.client) {
      sessionStorage.removeItem('taskflow-access-token')
    }
  }

  async function carregarUtilizador(): Promise<AuthUser> {
    const atual = await api<AuthUser>('/auth/me')
    user.value = atual
    return atual
  }

  async function login(email: string, password: string): Promise<AuthUser> {
    const config = useRuntimeConfig()
    const apiBase = String(config.public.apiBase).replace(/\/+$/, '')
    const form = new URLSearchParams({
      username: email.trim().toLowerCase(),
      password,
    })
    const resposta = await $fetch<LoginResponse>(`${apiBase}/auth/login`, {
      method: 'POST',
      body: form,
    })

    guardarToken(resposta.access_token)
    try {
      return await carregarUtilizador()
    } catch (error) {
      limparSessao()
      throw error
    }
  }

  async function logout(): Promise<void> {
    limparSessao()
    await navigateTo('/login')
  }

  return {
    user,
    token,
    login,
    logout,
    limparSessao,
    carregarUtilizador,
    guardarToken,
  }
}
