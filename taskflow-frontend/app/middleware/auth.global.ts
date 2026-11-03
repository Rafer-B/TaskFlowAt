export default defineNuxtRouteMiddleware(async (to) => {
  // A validação da sessão depende do armazenamento do navegador e só ocorre no cliente.
  if (import.meta.server) return

  const auth = useAuth()
  const token = sessionStorage.getItem('taskflow-access-token')
  const isLoginPage = to.path === '/login'

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
    // Além de autenticar, carrega o papel usado abaixo para limitar rotas administrativas.
    const user = await auth.carregarUtilizador()

    if (isLoginPage) {
      return navigateTo(user.role === 'admin' ? '/' : '/front-office')
    }

    const adminOnlyPaths = ['/', '/users', '/reports']
    const isAdminOnly = adminOnlyPaths.some(
      (path) =>
        to.path === path ||
        (path !== '/' && to.path.startsWith(`${path}/`)),
    )

    if (isAdminOnly && user.role !== 'admin') {
      return navigateTo(to.path === '/' ? '/front-office' : '/projects')
    }
  } catch (error) {
    console.error('Não foi possível validar a sessão:', error)
    auth.limparSessao()
    if (!isLoginPage) {
      return navigateTo('/login')
    }
  }
})
