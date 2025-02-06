import api from './api'

export default {
  // Get all services
  getServices() {
    return api.get('/admin/services', {
      params: {
        timestamp: new Date().getTime() // Add timestamp to prevent caching
      }
    })
  },

  // Get service categories
  getServiceCategories() {
    return api.get('/services/categories/', {
      params: {
        timestamp: new Date().getTime() // Add timestamp to prevent caching
      }
    })
  },

  // Get service requests with filters
  getServiceRequests(params = {}) {
    return api.get('/admin/requests', { 
      params: {
        ...params,
        timestamp: new Date().getTime() // Add timestamp to prevent caching
      }
    })
  },

  // Get professionals with filters
  getProfessionals(params = {}) {
    return api.get('/admin/professionals', { 
      params: {
        ...params,
        timestamp: new Date().getTime() // Add timestamp to prevent caching
      }
    })
  },

  // Get customers with filters
  getCustomers(params = {}) {
    return api.get('/admin/customers', { 
      params: {
        ...params,
        timestamp: new Date().getTime() // Add timestamp to prevent caching
      }
    })
  },

  // Update user status (block/unblock)
  updateUserStatus(userId, active) {
    return api.put(`/admin/users/${userId}/status`, { active })
  },

  // Verify or reject professional
  async verifyProfessional(professionalId, { approved, comment }) {
    try {
      const { data } = await api.post(`/admin/professionals/${professionalId}/verify`, { approved, comment })
      return data
    } catch (error) {
      throw error
    }
  },

  // Get professional documents
  getProfessionalDocuments(professionalId) {
    return api.get(`/admin/professionals/${professionalId}/documents`)
  },

  // Get dashboard stats
  getDashboardStats() {
    return api.get('/admin/dashboard/stats', {
      params: {
        timestamp: new Date().getTime()
    })
  },

  // Create new service
  createService(serviceData) {
    return api.post('/services/', serviceData)
  },

  // Update service
  updateService(serviceId, serviceData) {
    return api.put(`/services/${serviceId}/`, serviceData)
  },

  // Delete service
  deleteService(serviceId) {
    return api.delete(`/services/${serviceId}/`)
  },

  // Assign professional to request
  assignRequest(requestId, professionalId) {
    return api.post(`/admin/requests/${requestId}/assign`, { professional_id: professionalId })
  },

  // Unassign professional from request
  unassignRequest(requestId) {
    return api.post(`/admin/requests/${requestId}/unassign`)
  },

  // Export service requests
  async exportServiceRequests(professionalId) {
    try {
      const response = await api.post(`/admin/export/service-requests/${professionalId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
}
