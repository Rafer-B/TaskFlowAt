export function obterUrlAvatar(
  avatarUrl: string | null | undefined,
  apiBase: string,
): string {
  // Ausência de fotografia devolve cadeia vazia para permitir fallback para iniciais.
  if (!avatarUrl) return ''

  // URLs absolutas não devem ser prefixadas com o endereço da API.
  if (avatarUrl.startsWith('http://') || avatarUrl.startsWith('https://')) {
    return avatarUrl
  }

  return `${apiBase.replace(/\/+$/, '')}/${avatarUrl.replace(/^\/+/, '')}`
}
