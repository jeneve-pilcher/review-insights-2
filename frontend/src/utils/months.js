export const MAX_MONTHS = 60

// Whole numbers only: "6" and "07" are fine; "", "0", "2.5", "1e1", "-3", "abc" and "61" are not.
export function parseMonths(text, max = MAX_MONTHS) {
  const trimmed = String(text ?? '').trim()
  const message = `Enter a whole number of months between 1 and ${max}.`
  if (!/^\d+$/.test(trimmed)) return { valid: false, value: null, message }
  const value = Number(trimmed)
  if (value < 1 || value > max) return { valid: false, value: null, message }
  return { valid: true, value, message: '' }
}
