import axios from 'axios'
import { supabase } from './supabase'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL })

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const token = data?.session?.access_token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function fetchMe() {
  const { data } = await api.get('/api/me')
  return data
}

export async function setBusinessLocation(businessLocation) {
  const { data } = await api.post('/api/me/business-location', {
    business_location: businessLocation,
  })
  return data
}

// ONE request, ONE review pull for your business, powers every panel. Any competitors
// you list are the only extra pulls (one each).
export async function analyzeAll({
  months,
  avgOrderValue,
  reviewsToCustomersMultiplier,
  competitors = [],
  sources = ['google'],
  view = 'combined',
  mentions = false,
  mentionTerms = null,
  mentionPages = 2,
}) {
  const { data } = await api.post('/api/analyze/all', {
    months,
    avg_order_value: avgOrderValue,
    reviews_to_customers_multiplier: reviewsToCustomersMultiplier,
    competitors,
    sources,
    view,
    mentions,
    mention_terms: mentionTerms,
    mention_pages: mentionPages,
  })
  return data
}

export async function setPlatformUrl(platform, url) {
  const { data } = await api.post('/api/me/platform-url', { platform, url })
  return data
}

// Saves several review-page links at once (all or nothing). Returns { links: { yelp_url: ..., ... } }.
export async function saveLinks(links) {
  const { data } = await api.post('/api/me/links', links)
  return data
}

export async function setYelpUrl(yelpUrl) {
  const { data } = await api.post('/api/me/yelp-url', { yelp_url: yelpUrl })
  return data
}

export async function deleteAccount() {
  const { data } = await api.delete('/api/me')
  return data
}

export async function createCheckoutSession() {
  const { data } = await api.post('/api/billing/create-checkout-session')
  return data
}

export async function createPortalSession() {
  const { data } = await api.post('/api/billing/create-portal-session')
  return data
}

export async function submitEnterpriseContact(payload) {
  const { data } = await api.post('/api/enterprise-contact', payload)
  return data
}

// ---- Company (multi-location) console ----
export const orgApi = {
  async get() { return (await api.get('/api/org')).data },
  async create(name) { return (await api.post('/api/org', { name })).data },
  async setIndustry(industry) {
    return (await api.put('/api/org/industry', { industry })).data
  },
  // Individual-doctor numbers for one location (only what this person's role may see).
  async providers(locationId) {
    return (await api.get(`/api/org/locations/${locationId}/providers`)).data
  },
  // Industry numbers for the company: headline numbers, theme grid, rankings, trend, OpenTable scores by location.
  async industry() {
    return (await api.get('/api/org/industry')).data
  },
  // Dollars of credit per month, or null for no limit.
  async setBudget(monthlyBudgetUsd) {
    return (await api.patch('/api/org/budget', { monthly_budget_usd: monthlyBudgetUsd })).data
  },

  async addMember(email, role) { return (await api.post('/api/org/members', { email, role })).data },
  async updateMember(id, role) { return (await api.patch(`/api/org/members/${id}`, { role })).data },
  async removeMember(id) { return (await api.delete(`/api/org/members/${id}`)).data },

  async locations() { return (await api.get('/api/org/locations')).data },
  async addLocation(body) { return (await api.post('/api/org/locations', body)).data },
  async importLocations(csvText) { return (await api.post('/api/org/locations/import', { csv_text: csvText })).data },
  async updateLocation(id, body) { return (await api.patch(`/api/org/locations/${id}`, body)).data },
  async deleteLocation(id) { return (await api.delete(`/api/org/locations/${id}`)).data },
  async runLocation(id) { return (await api.post(`/api/org/locations/${id}/run`)).data },
  async history(id) { return (await api.get(`/api/org/locations/${id}/history`)).data },
  async analysis(id, months = 6, view = 'combined', mentions = false) {
    return (await api.get(`/api/org/locations/${id}/analysis`, { params: { months, view, mentions } })).data
  },

  async overview() { return (await api.get('/api/org/overview')).data },
  async benchmarks(groupBy = 'all') { return (await api.get('/api/org/benchmarks', { params: { group_by: groupBy } })).data },
  async alerts(status) { return (await api.get('/api/org/alerts', { params: status ? { status } : {} })).data },
  async updateAlert(id, body) { return (await api.patch(`/api/org/alerts/${id}`, body)).data },
  async audit() { return (await api.get('/api/org/audit')).data },
}

// ---- Review replies (drafts and what's been answered) ----
export const repliesApi = {
  async list(locationId) {
    return (await api.get('/api/replies', { params: locationId ? { location_id: locationId } : {} })).data
  },
  async draft(body) { return (await api.post('/api/replies/draft', body)).data },
  async save(body) { return (await api.put('/api/replies', body)).data },
}

// ---- Usage credit ----
export const creditsApi = {
  async get(scope = 'user') { return (await api.get('/api/credits', { params: { scope } })).data },
  async checkout(packId, scope = 'user') { return (await api.post('/api/credits/checkout', { pack_id: packId, scope })).data },
  async confirm(sessionId) { return (await api.post('/api/credits/confirm', { session_id: sessionId })).data },
  // Monthly spending limit in dollars of API usage; null = no limit.
  async setLimit(monthlyLimitUsd, scope = 'user') { return (await api.put('/api/credits/limit', { scope, monthly_limit_usd: monthlyLimitUsd })).data },
}

// ---- Branding and industry ----
// Public (no sign-in needed): a company's branding, found from a work email's domain.
export async function fetchBranding(email) {
  const { data } = await api.get('/api/branding', { params: { email } })
  return data
}

export async function fetchIndustries() {
  return (await api.get('/api/industries')).data
}

export async function setIndustry(industry) {
  return (await api.put('/api/me/industry', { industry })).data
}

export async function acceptTerms(version) {
  const { data } = await api.post('/api/me/accept-terms', { version })
  return data
}
