// Centraliza as fronteiras entre o back-office global e as páginas colaborativas.
export type PlatformRole = 'admin' | 'member'

const BACK_OFFICE_PATHS = ['/', '/users', '/reports'] as const

export function isBackOfficePath(path: string): boolean {
  return BACK_OFFICE_PATHS.some((basePath) =>
    basePath === '/'
      ? path === basePath
      : path === basePath || path.startsWith(`${basePath}/`),
  )
}

export function homeForRole(role: PlatformRole): '/' | '/my-work' {
  return role === 'admin' ? '/' : '/my-work'
}