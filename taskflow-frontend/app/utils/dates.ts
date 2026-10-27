// Funções auxiliares para trabalhar com datas no formato YYYY-MM-DD.
// Todas usam a hora local e ignoram a hora do dia, para evitar problemas de fuso horário.

export function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

export function addDays(date: Date, days: number): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days)
}

export function toISODay(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${date.getFullYear()}-${month}-${day}`
}

export function parseISODay(iso: string): Date {
  const [year, month, day] = iso.split('-').map(Number) as [number, number, number]

  return new Date(year, month - 1, day)
}

// Número de dias entre duas datas (positivo se "to" for depois de "from").
export function diffInDays(from: Date, to: Date): number {
  return Math.round((to.getTime() - from.getTime()) / 86_400_000)
}
