/**
 * Bloomberg-style number formatting helpers.
 * Thousands separated by THIN SPACES (not commas), tabular nums.
 */

const THIN_SPACE = ' '

export function formatNum(n: number | null | undefined, decimals = 2): string {
  if (n == null || Number.isNaN(n)) return '——'
  const fixed = Math.abs(n).toFixed(decimals)
  const [intPart, decPart] = fixed.split('.')
  // group integer part with thin spaces every 3 digits from the right
  const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, THIN_SPACE)
  const out = decPart ? `${grouped}.${decPart}` : grouped
  return n < 0 ? `-${out}` : out
}

export function formatSigned(n: number | null | undefined, decimals = 2): string {
  if (n == null || Number.isNaN(n)) return '——'
  if (n === 0) return formatNum(0, decimals)
  const s = formatNum(n, decimals)
  return n > 0 ? `+${s}` : s
}

export function formatPct(n: number | null | undefined, decimals = 2): string {
  if (n == null || Number.isNaN(n)) return '——'
  return `${formatNum(n, decimals)}%`
}

export function formatPctSigned(n: number | null | undefined, decimals = 2): string {
  if (n == null || Number.isNaN(n)) return '——'
  const s = formatPct(Math.abs(n), decimals)
  if (n === 0) return s
  return n > 0 ? `+${s}` : `-${s}`
}

/** Format a Date as UTC `YYYY-MM-DD HH:mm:ss UTC`. */
export function formatUTC(d: Date = new Date()): string {
  const pad = (n: number) => (n < 10 ? '0' + n : String(n))
  return (
    d.getUTCFullYear() +
    '-' +
    pad(d.getUTCMonth() + 1) +
    '-' +
    pad(d.getUTCDate()) +
    ' ' +
    pad(d.getUTCHours()) +
    ':' +
    pad(d.getUTCMinutes()) +
    ':' +
    pad(d.getUTCSeconds()) +
    ' UTC'
  )
}

/** Format compact USD with proper unit (M, B). */
export function formatCompactUsd(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return '$——'
  const abs = Math.abs(n)
  if (abs >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
  if (abs >= 1e6) return `$${(n / 1e6).toFixed(2)}M`
  if (abs >= 1e3) return `$${(n / 1e3).toFixed(2)}K`
  return `$${n.toFixed(2)}`
}
