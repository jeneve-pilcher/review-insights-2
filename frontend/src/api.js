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
  })
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
  async setBudget(monthlyBudgetReviews) {
    return (await api.patch('/api/org/budget', { monthly_budget_reviews: monthlyBudgetReviews })).data
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

export async function acceptTerms(version) {
  const { data } = await api.post('/api/me/accept-terms', { version })
  return data
}
