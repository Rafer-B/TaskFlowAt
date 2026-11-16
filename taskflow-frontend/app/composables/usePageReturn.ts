type PageQuery = Record<string, string | number | boolean | undefined>

function isInternalReturnPath(value: unknown): value is string {
  return typeof value === 'string' &&
    value.startsWith('/') &&
    !value.startsWith('//') &&
    !value.includes('\\')
}

export function usePageReturn() {
  const route = useRoute()

  function returnPath(fallback: string): string {
    const value = route.query.returnTo
    return isInternalReturnPath(value) ? value : fallback
  }

  function pageLink(
    path: string,
    query: PageQuery = {},
    from = route.fullPath,
  ) {
    return {
      path,
      query: {
        ...query,
        returnTo: from,
      },
    }
  }

  function openPage(
    path: string,
    query: PageQuery = {},
    from = route.fullPath,
  ) {
    return navigateTo(pageLink(path, query, from))
  }

  function closePage(fallback: string) {
    return navigateTo(returnPath(fallback))
  }

  return { closePage, openPage, pageLink, returnPath }
}
