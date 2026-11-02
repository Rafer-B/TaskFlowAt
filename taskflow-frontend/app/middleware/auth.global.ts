export default defineNuxtRouteMiddleware(async (to) => {
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
    const user = await auth.carregarUtilizador()

    if (isLoginPage) {
      return navigateTo(user.role === 'admin' ? '/' : '/my-work')
    }

    const backOfficePaths = ['/', '/projects', '/tasks', '/users', '/settings']
    const isBackOffice = backOfficePaths.some(
      (path) =>
        to.path === path ||
        (path !== '/' && to.path.startsWith(`${path}/`)),
    )

    if (isBackOffice && user.role !== 'admin') {
      return navigateTo('/my-work')
    }
  } catch (error) {
    console.error('Não foi possível validar a sessão:', error)
    auth.limparSessao()
    if (!isLoginPage) {
      return navigateTo('/login')
    }
  }
})
