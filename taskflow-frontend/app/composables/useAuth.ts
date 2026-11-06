import type { PlatformRole } from '~/utils/access'

export interface AuthUser {
  id: number
  name: string
  email: string
  role: PlatformRole
  avatar_url: string | null
  is_active: boolean
  created_at: string
}

// Resposta mínima usada no início da sessão; os dados completos vêm de /auth/me.
interface LoginResponse {
  access_token: string
  token_type: 'bearer'
}

interface SavedAccountSession {
  user: AuthUser
  token: string
}

const ACCESS_TOKEN_KEY = 'taskflow-access-token'
const SAVED_ACCOUNTS_KEY = 'taskflow-saved-accounts'

export function useAuth() {
  // useState partilha a sessão entre componentes, mantendo o token apenas em memória/aba.
  const user = useState<AuthUser | null>('taskflow-auth-user', () => null)
  const token = useState<string>('taskflow-auth-token', () => '')
  const api = useNuxtApp().$api

  function carregarContasGuardadas(): SavedAccountSession[] {
    if (import.meta.server) return []

    try {
      const saved = JSON.parse(sessionStorage.getItem(SAVED_ACCOUNTS_KEY) ?? '[]')
      if (!Array.isArray(saved)) return []

      return saved.filter((entry): entry is SavedAccountSession =>
        typeof entry === 'object' && entry !== null &&
        typeof entry.token === 'string' &&
        typeof entry.user === 'object' && entry.user !== null &&
        typeof entry.user.id === 'number' &&
        typeof entry.user.name === 'string' &&
        typeof entry.user.email === 'string' &&
        (entry.user.role === 'admin' || entry.user.role === 'member'),
      )
    } catch {
      return []
    }
  }

  function guardarContasGuardadas(contas: SavedAccountSession[]): void {
    if (import.meta.client) {
      sessionStorage.setItem(SAVED_ACCOUNTS_KEY, JSON.stringify(contas))
    }
  }

  function guardarSessaoAtual(atual: AuthUser, accessToken: string): void {
    const restantes = carregarContasGuardadas().filter(
      (conta) => conta.user.id !== atual.id,
    )
    guardarContasGuardadas([{ user: atual, token: accessToken }, ...restantes])
  }

  function removerContaGuardada(userId: number): void {
    guardarContasGuardadas(
      carregarContasGuardadas().filter((conta) => conta.user.id !== userId),
    )
  }

  function guardarToken(value: string) {
    if (import.meta.client) {
      sessionStorage.setItem(ACCESS_TOKEN_KEY, value)
    }
    token.value = value
  }

  function limparSessao() {
    token.value = ''
    user.value = null
    if (import.meta.client) {
      sessionStorage.removeItem(ACCESS_TOKEN_KEY)
    }
  }

  async function carregarUtilizador(): Promise<AuthUser> {
    // Revalida o token no servidor e sincroniza o perfil atual da conta.
    const atual = await api<AuthUser>('/auth/me')
    user.value = atual
    if (token.value) guardarSessaoAtual(atual, token.value)
    return atual
  }

  async function login(email: string, password: string): Promise<AuthUser> {
    const config = useRuntimeConfig()
    const apiBase = String(config.public.apiBase).replace(/\/+$/, '')
    // O endpoint de autenticação espera credenciais como formulário URL-encoded.
    const form = new URLSearchParams({
      username: email.trim().toLowerCase(),
      password,
    })
    const resposta = await $fetch<LoginResponse>(`${apiBase}/auth/login`, {
      method: 'POST',
      body: form,
    })

    // Valida a nova conta sem substituir a sessão atual, usada ao adicionar contas.
    const atual = await $fetch<AuthUser>(`${apiBase}/auth/me`, {
      headers: {
        Authorization: `Bearer ${resposta.access_token}`,
      },
    })

    guardarSessaoAtual(atual, resposta.access_token)
    guardarToken(resposta.access_token)
    user.value = atual
    return atual
  }

  async function logout(): Promise<void> {
    limparSessao()
    if (import.meta.client) {
      sessionStorage.removeItem(SAVED_ACCOUNTS_KEY)
    }
    await navigateTo('/login')
  }

  async function trocarConta(userId: number): Promise<AuthUser> {
    const conta = carregarContasGuardadas().find(
      (item) => item.user.id === userId,
    )
    if (!conta) throw new Error('A conta selecionada já não está disponível nesta sessão.')

    const tokenAnterior = token.value
    const utilizadorAnterior = user.value
    guardarToken(conta.token)

    try {
      return await carregarUtilizador()
    } catch (error) {
      removerContaGuardada(userId)

      if (tokenAnterior && utilizadorAnterior) {
        guardarToken(tokenAnterior)
        user.value = utilizadorAnterior
      } else {
        limparSessao()
      }
      throw error
    }
  }

  return {
    user,
    token,
    login,
    logout,
    trocarConta,
    carregarContasGuardadas,
    limparSessao,
    carregarUtilizador,
    guardarToken,
  }
}
