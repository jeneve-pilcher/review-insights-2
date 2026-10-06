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
export async function analyzeAll({ months, avgOrderValue, reviewsToCustomersMultiplier, competitors = [] }) {
  const { data } = await api.post('/api/analyze/all', {
    months,
    avg_order_value: avgOrderValue,
    reviews_to_customers_multiplier: reviewsToCustomersMultiplier,
    competitors,
  })
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
