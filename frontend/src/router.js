import { createRouter, createWebHistory } from 'vue-router'
import { supabase } from './supabase'

import DashboardView from './views/DashboardView.vue'
import EnterpriseContactView from './views/EnterpriseContactView.vue'
import LandingView from './views/LandingView.vue'
import LoginView from './views/LoginView.vue'
import SignupView from './views/SignupView.vue'
import AuthCallbackView from './views/AuthCallbackView.vue'
import ForgotPasswordView from './views/ForgotPasswordView.vue'
import ResetPasswordView from './views/ResetPasswordView.vue'

const routes = [
  { path: '/', name: 'landing', component: LandingView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/signup', name: 'signup', component: SignupView },
  { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView },
  { path: '/reset-password', name: 'reset-password', component: ResetPasswordView },
  { path: '/enterprise', name: 'enterprise', component: EnterpriseContactView },
  { path: '/auth/callback', name: 'auth-callback', component: AuthCallbackView },
  { path: '/dashboard', name: 'dashboard', component: DashboardView, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true

  const { data } = await supabase.auth.getSession()
  if (!data?.session) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
