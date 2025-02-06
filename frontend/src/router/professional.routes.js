// src/router/professional.routes.js
export const professionalRoutes = [
  {
    path: '/professional/dashboard',
    name: 'professional.dashboard',
    component: () => import('@/views/professional/DashboardView.vue'),
    meta: {
      requiresAuth: true,
      requiresProfessional: true
    }
  },
  {
    path: '/professional/profile',
    name: 'professional.profile',
    component: () => import('@/views/professional/ProfileView.vue'),
    meta: {
      requiresAuth: true,
      requiresProfessional: true
    }
  },
  {
    path: '/professional/summary',
    name: 'professional.summary',
    component: () => import('@/views/professional/SummaryView.vue'),
    meta: {
      requiresAuth: true,
      requiresProfessional: true
    }
  }
]
