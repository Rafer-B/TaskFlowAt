export function obterUrlAvatar(
  avatarUrl: string | null | undefined,
  apiBase: string,
): string {
  if (!avatarUrl) return ''

  if (avatarUrl.startsWith('http://') || avatarUrl.startsWith('https://')) {
    return avatarUrl
  }

  return `${apiBase.replace(/\/+$/, '')}/${avatarUrl.replace(/^\/+/, '')}`
}
