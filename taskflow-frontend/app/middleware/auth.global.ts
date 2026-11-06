import { homeForRole, isBackOfficePath } from '~/utils/access'

export default defineNuxtRouteMiddleware(async (to) => {
  // A validação da sessão depende do armazenamento do navegador e só ocorre no cliente.
  if (import.meta.server) return

  const auth = useAuth()
  const token = sessionStorage.getItem('taskflow-access-token')
  const isLoginPage = to.path === '/login'
  const isAddingAccount = to.query.switchAccount === '1'

  if (!token) {
    auth.limparSessao()
    if (!isLoginPage) {
      return navigateTo({
        path: '/login',
        query: to.path === '/' ? undefined : { redirect: to.fullPath },
      })
    }
    return
  }

  auth.guardarToken(token)

  try {
    // Além de autenticar, carrega o papel usado abaixo para limitar rotas de back-office.
    const user = await auth.carregarUtilizador()

    if (isLoginPage && !isAddingAccount) {
      return navigateTo(homeForRole(user.role))
    }

    if (isBackOfficePath(to.path) && user.role !== 'admin') {
      return navigateTo(homeForRole(user.role))
    }
  } catch (error) {
    console.error('Não foi possível validar a sessão:', error)
    auth.limparSessao()
    if (!isLoginPage) {
      return navigateTo('/login')
    }
  }
})
