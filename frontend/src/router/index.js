// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/auth/LoginView.vue'
import RegisterView from '@/views/auth/RegisterView.vue'
import UnauthorizedView from '@/views/auth/UnauthorizedView.vue'
import { customerRoutes } from './customer.routes'
import { professionalRoutes } from './professional.routes'
import { adminRoutes } from './admin.routes'
import store from '@/store'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { guestOnly: true }
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { guestOnly: true }
  },
  {
    path: '/unauthorized',
    name: 'unauthorized',
    component: UnauthorizedView
  },
  ...customerRoutes,
  ...professionalRoutes,
  ...adminRoutes
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  // Initialize auth state if needed
  if (!store.state.auth.user && store.state.auth.token) {
    try {
      await store.dispatch('auth/initialize')
    } catch (error) {
      store.commit('auth/clearAuth')
      return next({
        name: 'login',
        query: { redirect: to.fullPath }
      })
    }
  }

  const isAuthenticated = store.getters['auth/isAuthenticated']
  const userType = store.getters['auth/userType']

  // Redirect from root path based on user type if authenticated
  if ((to.path === '/' || to.path === '/dashboard') && isAuthenticated) {
    if (userType === 'customer') {
      return next('/customer/dashboard')
    } else if (userType === 'professional') {
      return next('/professional/dashboard')
    } else if (userType === 'admin') {
      return next('/admin')
    }
  }

  // Handle guest-only routes
  if (to.meta.guestOnly && isAuthenticated) {
    if (userType === 'customer') {
      return next('/customer/dashboard')
    } else if (userType === 'professional') {
      return next('/professional/dashboard')
    } else if (userType === 'admin') {
      return next('/admin')
    }
  }

  // If route doesn't require auth, proceed
  if (!to.meta.requiresAuth && 
      !to.meta.requiresCustomer && 
      !to.meta.requiresProfessional &&
      !to.meta.requiresAdmin) {
    return next()
  }

  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    return next({
      name: 'login',
      query: { redirect: to.fullPath }
    })
  }

  // Handle user type specific routes
  if (to.meta.requiresAdmin && userType !== 'admin') {
    return next('/unauthorized')
  }
  if (to.meta.requiresCustomer && userType !== 'customer') {
    return next('/unauthorized')
  }
  if (to.meta.requiresProfessional && userType !== 'professional') {
    return next('/unauthorized')
  }

  next()
})

export default router
