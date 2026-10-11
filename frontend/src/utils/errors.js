// Turns a failed request into something a person can act on, instead of a generic "could not load".
export function explainError(err, what) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string' && detail) return detail
  const status = err?.response?.status
  if (status) {
    return `${what} (the server returned error ${status}). If you just updated the app, run backend/supabase/corporate.sql in Supabase, restart the backend, and reload. Details are in the backend log.`
  }
  return `${what}. The app couldn't reach the server, so check that the backend is running.`
}
