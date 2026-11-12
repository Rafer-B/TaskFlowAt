import { homeForRole, isBackOfficePath } from '~/utils/access'

export default defineNuxtRouteMiddleware(async (to) => {
  // A sessão fica num cookie HttpOnly; só o browser pode validar o estado atual.
  if (import.meta.server) return

  const auth = useAuth()
  const isLoginPage = to.path === '/login'
  const isPublicPage = isLoginPage || to.path === '/password-reset'
  const isAddingAccount = to.query.switchAccount === '1'

  try {
    const user = await auth.carregarUtilizador()

    if (isLoginPage && !isAddingAccount) {
      return navigateTo(homeForRole(user.role))
    }

    if (isBackOfficePath(to.path) && user.role !== 'admin') {
      return navigateTo(homeForRole(user.role))
    }
  } catch {
    auth.limparSessao()
    if (!isPublicPage) {
      return navigateTo({
        path: '/login',
        query: to.path === '/' ? undefined : { redirect: to.fullPath },
      })
    }
  }
})
