import { shortBusinessName } from './placeName'

const isUrl = (text) => /^https?:\/\//i.test(String(text ?? '').trim())

// Turns the competitor rows into what gets sent. People paste a Google Maps link into whichever box is nearest, so:
//  - a row with only one box filled uses that box as the location (the link or the "name, street, city"),
//  - a link typed into the name box is the location, and the name is read out of the link,
//  - rows with nothing in either box are left out.
export function normalizeCompetitors(rows) {
  const out = []
  ;(rows ?? []).forEach((row, i) => {
    let name = String(row?.name ?? '').trim()
    let query = String(row?.search_query ?? '').trim()
    // "Competitor 3" is only the pre-filled label, not something the person typed.
    const labelOnly = /^competitor \d+$/i.test(name)
    if (!query && name && !labelOnly) query = name
    if (!query) return
    if (!name || labelOnly || isUrl(name) || name === query) {
      const fromLink = isUrl(query) ? shortBusinessName(query) : query.split(',')[0].trim()
      name = fromLink && fromLink !== 'your business' ? fromLink : `Competitor ${i + 1}`
    }
    out.push({ name, search_query: query })
  })
  return out
}
