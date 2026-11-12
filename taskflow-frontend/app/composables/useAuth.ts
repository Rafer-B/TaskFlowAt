import type { PlatformRole } from '~/utils/access'

export interface AuthUser {
  id: string
  name: string
  email: string
  role: PlatformRole
  avatar_url: string | null
  is_active: boolean
  created_at: string
}

interface SavedAccount {
  user: AuthUser
}

const SAVED_ACCOUNTS_KEY = 'taskflow-saved-accounts'

export function useAuth() {
  const user = useState<AuthUser | null>('taskflow-auth-user', () => null)
  const api = useNuxtApp().$api

  function carregarContasGuardadas(): SavedAccount[] {
    if (import.meta.server) return []

    try {
      const saved: unknown = JSON.parse(
        sessionStorage.getItem(SAVED_ACCOUNTS_KEY) ?? '[]',
      )
      if (!Array.isArray(saved)) return []

      return saved.filter((entry): entry is SavedAccount =>
        typeof entry === 'object' &&
        entry !== null &&
        typeof entry.user === 'object' &&
        entry.user !== null &&
        typeof entry.user.id === 'string' &&
        typeof entry.user.name === 'string' &&
        typeof entry.user.email === 'string' &&
        (entry.user.role === 'admin' || entry.user.role === 'member'),
      )
    } catch (error) {
      console.error('Não foi possível ler as contas guardadas:', error)
      return []
    }
  }

  function guardarConta(atual: AuthUser): void {
    if (!import.meta.client) return
    const restantes = carregarContasGuardadas().filter(
      (conta) => conta.user.id !== atual.id,
    )
    sessionStorage.setItem(
      SAVED_ACCOUNTS_KEY,
      JSON.stringify([{ user: atual }, ...restantes]),
    )
  }

  function limparSessao(): void {
    user.value = null
  }

  async function carregarUtilizador(): Promise<AuthUser> {
    const atual = await api<AuthUser>('/auth/me')
    user.value = atual
    guardarConta(atual)
    return atual
  }

  async function login(email: string, password: string): Promise<AuthUser> {
    const form = new URLSearchParams({
      username: email.trim().toLowerCase(),
      password,
    })
    const atual = await api<AuthUser>('/auth/login', {
      method: 'POST',
      body: form,
    })
    user.value = atual
    guardarConta(atual)
    return atual
  }

  async function logout(): Promise<void> {
    await api('/auth/logout', { method: 'POST' })
    limparSessao()
    if (import.meta.client) {
      sessionStorage.removeItem(SAVED_ACCOUNTS_KEY)
    }
    await navigateTo('/login')
  }

  return {
    user,
    login,
    logout,
    carregarContasGuardadas,
    limparSessao,
    carregarUtilizador,
  }
}
