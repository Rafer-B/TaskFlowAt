export type ThemeId = 'calm' | 'cool' | 'warm'

export interface InterfacePreferences {
  theme: ThemeId
  reducedMotion: boolean
}

export const INTERFACE_PREFERENCES_KEY = 'taskflow-interface-preferences'

export const themes: Array<{
  id: ThemeId
  name: string
  description: string
  background: string
  surface: string
}> = [
  {
    id: 'calm',
    name: 'Verde suave',
    description: 'Um fundo verde acinzentado e superfícies suaves para reduzir o brilho.',
    background: '#e8ece6',
    surface: '#f4f5f1',
  },
  {
    id: 'cool',
    name: 'Cinza azulado',
    description: 'Uma tonalidade fria e discreta, confortável para o uso diário.',
    background: '#e7ecf1',
    surface: '#f3f5f8',
  },
  {
    id: 'warm',
    name: 'Areia clara',
    description: 'Um tom quente e suave, mantendo o texto e os controlos bem visíveis.',
    background: '#eee8df',
    surface: '#f7f3ec',
  },
]

export function isThemeId(value: unknown): value is ThemeId {
  return themes.some(theme => theme.id === value)
}

export function aplicarAparencia(preferencias: InterfacePreferences): void {
  const tema = themes.find(option => option.id === preferencias.theme)
  if (!tema) return

  document.documentElement.style.setProperty('--tf-bg', tema.background)
  document.documentElement.style.setProperty('--tf-surface', tema.surface)
  document.documentElement.dataset.reducedMotion = String(
    preferencias.reducedMotion,
  )
}
