
/**
 * Funções auxiliares para trabalhar com datas.
 * Os cálculos de dias utilizam a hora local.
 */

export function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

export function addDays(date: Date, days: number): Date {
  return new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate() + days,
  )
}

export function toISODay(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${date.getFullYear()}-${month}-${day}`
}

export function parseISODay(iso: string): Date {
  const [year, month, day] = iso.split('-').map(Number) as [
    number,
    number,
    number,
  ]

  return new Date(year, month - 1, day)
}

// Diferença em dias, ignorando as horas.
export function diffInDays(from: Date, to: Date): number {
  const inicio = startOfDay(from).getTime()
  const fim = startOfDay(to).getTime()

  return Math.round((fim - inicio) / 86_400_000)
}

// Formata uma data como 30/10/2026.
export function formatarData(
  valor: string | Date | null | undefined,
): string {
  if (!valor) return 'Sem data'

  const data =
    valor instanceof Date
      ? valor
      : /^\d{4}-\d{2}-\d{2}$/.test(valor)
        ? parseISODay(valor)
        : new Date(valor)

  if (Number.isNaN(data.getTime())) return 'Data inválida'

  return new Intl.DateTimeFormat('pt-PT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(data)
}

// Formata data e hora como 30/10/2026, 09:03.
export function formatarDataHora(
  valor: string | Date | null | undefined,
): string {
  if (!valor) return 'Sem data'

  const data = valor instanceof Date ? valor : new Date(valor)

  if (Number.isNaN(data.getTime())) return 'Data inválida'

  return new Intl.DateTimeFormat('pt-PT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(data)
}
