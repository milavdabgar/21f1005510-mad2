export const adminRoutes = [
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'admin-dashboard',
        component: () => import('@/views/admin/DashboardView.vue')
      },
      {
        path: 'services',
        name: 'admin-services',
        component: () => import('@/views/admin/ServicesView.vue')
      },
      {
        path: 'professionals',
        name: 'admin-professionals',
        component: () => import('@/views/admin/ProfessionalsView.vue')
      },
      {
        path: 'customers',
        name: 'admin-customers',
        component: () => import('@/views/admin/CustomersView.vue')
      },
      {
        path: 'requests',
        name: 'admin-requests',
        component: () => import('@/views/admin/ServiceRequestsView.vue')
      }
    ]
  }
]
