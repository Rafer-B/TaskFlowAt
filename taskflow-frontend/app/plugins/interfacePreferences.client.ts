import {
  INTERFACE_PREFERENCES_KEY,
  aplicarAparencia,
  isThemeId,
  type InterfacePreferences,
} from '~/utils/interfacePreferences'

export default defineNuxtPlugin(() => {
  const preferencias: InterfacePreferences = {
    theme: 'calm',
    reducedMotion: false,
  }

  try {
    const stored = localStorage.getItem(INTERFACE_PREFERENCES_KEY)
    if (stored) {
      const parsed: unknown = JSON.parse(stored)
      if (typeof parsed === 'object' && parsed !== null) {
        if ('theme' in parsed && isThemeId(parsed.theme)) {
          preferencias.theme = parsed.theme
        }
        if (
          'reducedMotion' in parsed &&
          typeof parsed.reducedMotion === 'boolean'
        ) {
          preferencias.reducedMotion = parsed.reducedMotion
        }
      }
    }
  } catch (error) {
    console.error('Não foi possível carregar as preferências visuais:', error)
  }

  aplicarAparencia(preferencias)
})
