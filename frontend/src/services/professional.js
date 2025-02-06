import api from './api'

const professionalService = {
  async getProfile() {
    const response = await api.get('/professionals/profile')
    return response.data
  },

  async updateProfile(profileData) {
    const response = await api.put('/professionals/profile', profileData)
    return response.data
  },

  async getRequests(params = {}) {
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime()
    const response = await api.get('/professionals/requests', { 
      params: {
        ...params,
        _t: timestamp
      }
    })
    return response.data
  },

  async acceptRequest(requestId) {
    const response = await api.post(`/professionals/requests/${requestId}/accept`)
    return response.data
  },

  async rejectRequest(requestId) {
    const response = await api.post(`/professionals/requests/${requestId}/reject`)
    return response.data
  },

  async completeRequest(requestId) {
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime()
    const response = await api.post(`/professionals/requests/${requestId}/complete`, null, {
      params: { _t: timestamp }
    })
    return response.data
  },

  async updateAvailability(available) {
    const response = await api.put('/professionals/availability', { available })
    return response.data
  },

  async getDocuments() {
    const response = await api.get('/professionals/documents')
    return response.data
  },

  async uploadDocument(formData) {
    const response = await api.post('/professionals/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }
}

export default professionalService
