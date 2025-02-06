// src/router/customer.routes.js
export const customerRoutes = [
  {
    path: '/customer/dashboard',
    name: 'customer.dashboard',
    component: () => import('@/views/customer/DashboardView.vue'),
    meta: {
      requiresAuth: true,
      requiresCustomer: true
    }
  },
  {
    path: '/customer/services',
    name: 'customer.services',
    component: () => import('@/views/customer/ServicesView.vue'),
    meta: {
      requiresAuth: true,
      requiresCustomer: true
    }
  },
  {
    path: '/customer/requests',
    name: 'customer.requests',
    component: () => import('@/views/customer/RequestsView.vue'),
    meta: {
      requiresAuth: true,
      requiresCustomer: true
    }
  },
  {
    path: '/customer/summary',
    name: 'customer.summary',
    component: () => import('@/views/customer/SummaryView.vue'),
    meta: {
      requiresAuth: true,
      requiresCustomer: true
    }
  },
  {
    path: '/customer/profile',
    name: 'customer.profile',
    component: () => import('@/views/customer/ProfileView.vue'),
    meta: {
      requiresAuth: true,
      requiresCustomer: true
    }
  },
  {
    path: '/customer/requests/:id',
    name: 'customer.request-details',
    component: () => import('@/views/customer/RequestDetailsView.vue'),
    meta: {
      requiresAuth: true,
      requiresCustomer: true
    }
  }
]
