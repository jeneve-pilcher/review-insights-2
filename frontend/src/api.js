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

export async function analyzeSentimentDrift({ reviewLimit }) {
  const { data } = await api.post('/api/analyze/sentiment-drift', {
    review_limit: reviewLimit,
  })
  return data
}

export async function analyzeWaitTimeHeatmap({ reviewLimit, avgOrderValue, reviewsToCustomersMultiplier }) {
  const { data } = await api.post('/api/analyze/wait-time-heatmap', {
    review_limit: reviewLimit,
    avg_order_value: avgOrderValue,
    reviews_to_customers_multiplier: reviewsToCustomersMultiplier,
  })
  return data
}

export async function analyzeCompetitorShare({ competitors, reviewLimit }) {
  const { data } = await api.post('/api/analyze/competitor-share', {
    competitors,
    review_limit: reviewLimit,
  })
  return data
}

export async function analyzeAll({ reviewLimit, avgOrderValue, reviewsToCustomersMultiplier }) {
  const { data } = await api.post('/api/analyze/all', {
    review_limit: reviewLimit,
    avg_order_value: avgOrderValue,
    reviews_to_customers_multiplier: reviewsToCustomersMultiplier,
  })
  return data
}

export async function fetchNegativeReviews({ reviewLimit, lookbackDays, maxReviews }) {
  const { data } = await api.post('/api/analyze/negative-reviews', {
    review_limit: reviewLimit,
    lookback_days: lookbackDays,
    max_reviews: maxReviews,
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
