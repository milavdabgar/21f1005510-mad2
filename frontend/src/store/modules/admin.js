import adminService from '@/services/admin'
import { ref } from 'vue'

export default {
  namespaced: true,

  state: {
    services: [],
    serviceCategories: [],
    professionals: [],
    customers: [],
    serviceRequests: [],
    stats: null,
    professionalDocuments: null,
    loading: false,
    error: null
  },

  mutations: {
    SET_SERVICES(state, services) {
      // Create a new array and sort by newest first
      state.services = [...services].sort((a, b) => b.id - a.id)
    },
    SET_SERVICE_CATEGORIES(state, categories) {
      state.serviceCategories = categories
    },
    SET_PROFESSIONALS(state, professionals) {
      state.professionals = professionals
    },
    SET_CUSTOMERS(state, customers) {
      state.customers = customers
    },
    SET_SERVICE_REQUESTS(state, requests) {
      state.serviceRequests = requests
    },
    SET_STATS(state, stats) {
      state.stats = stats
    },
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    ADD_SERVICE(state, service) {
      state.services = [service, ...state.services]
    },
    UPDATE_SERVICE(state, updatedService) {
      const index = state.services.findIndex(s => s.id === updatedService.id)
      if (index !== -1) {
        const newServices = [...state.services]
        newServices.splice(index, 1, updatedService)
        state.services = newServices
      }
    },
    REMOVE_SERVICE(state, serviceId) {
      state.services = state.services.filter(s => s.id !== serviceId)
    },
    SET_PROFESSIONAL_DOCUMENTS(state, documents) {
      state.professionalDocuments = documents
    },
    UPDATE_REQUEST(state, updatedRequest) {
      const index = state.serviceRequests.findIndex(r => r.id === updatedRequest.id)
      if (index !== -1) {
        const newRequests = [...state.serviceRequests]
        newRequests.splice(index, 1, updatedRequest)
        state.serviceRequests = newRequests
      }
    }
  },

  actions: {
    async fetchServices({ commit }) {
      try {
        commit('SET_LOADING', true)
        const response = await adminService.getServices()
        const services = response.data.items || []
        commit('SET_SERVICES', services)
        return services
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async fetchServiceCategories({ commit }) {
      try {
        commit('SET_LOADING', true)
        const response = await adminService.getServiceCategories()
        const categories = response.data.items || []
        commit('SET_SERVICE_CATEGORIES', categories)
        return categories
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async createService({ commit }, serviceData) {
      try {
        commit('SET_LOADING', true)
        const response = await adminService.createService(serviceData)
        const newService = response.data
        commit('ADD_SERVICE', newService)
        return newService
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async updateService({ commit }, { id, ...serviceData }) {
      try {
        commit('SET_LOADING', true)
        const response = await adminService.updateService(id, serviceData)
        const updatedService = response.data
        commit('UPDATE_SERVICE', updatedService)
        return updatedService
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async deleteService({ commit }, id) {
      try {
        commit('SET_LOADING', true)
        await adminService.deleteService(id)
        commit('REMOVE_SERVICE', id)
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async fetchProfessionals({ commit }, params) {
      try {
        commit('SET_LOADING', true)
        const response = await adminService.getProfessionals(params)
        commit('SET_PROFESSIONALS', response.data.items)
      } catch (error) {
        commit('SET_ERROR', error.message)
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async fetchCustomers({ commit }, params) {
      try {
        commit('SET_LOADING', true)
        const response = await adminService.getCustomers(params)
        commit('SET_CUSTOMERS', response.data.items)
      } catch (error) {
        commit('SET_ERROR', error.message)
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async fetchServiceRequests({ commit }, params) {
      try {
        commit('SET_LOADING', true)
        const response = await adminService.getServiceRequests(params)
        commit('SET_SERVICE_REQUESTS', response.data.items)
      } catch (error) {
        commit('SET_ERROR', error.message)
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async fetchStats({ commit }) {
      try {
        commit('SET_LOADING', true)
        const response = await adminService.getDashboardStats()
        commit('SET_STATS', response.data)
      } catch (error) {
        commit('SET_ERROR', error.message)
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async updateUserStatus({ commit }, { userId, active }) {
      try {
        const response = await adminService.updateUserStatus(userId, active);
        return response;
      } catch (error) {
        console.error('Error updating user status:', error);
        throw error;
      }
    },

    async verifyProfessional({ commit }, { professionalId, approved, comment }) {
      try {
        commit('SET_LOADING', true)
        const data = await adminService.verifyProfessional(professionalId, { approved, comment })
        commit('SET_ERROR', null)
        return data
      } catch (error) {
        const errorMessage = error?.response?.data?.message || 'Error verifying professional'
        commit('SET_ERROR', errorMessage)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async fetchProfessionalDocuments({ commit }, professionalId) {
      try {
        commit('SET_LOADING', true)
        const response = await adminService.getProfessionalDocuments(professionalId)
        commit('SET_PROFESSIONAL_DOCUMENTS', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async assignRequest({ commit }, { requestId, professionalId }) {
      try {
        commit('SET_LOADING', true)
        const response = await adminService.assignRequest(requestId, professionalId)
        const updatedRequest = response.data
        commit('UPDATE_REQUEST', updatedRequest)
        return updatedRequest
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async unassignRequest({ commit }, requestId) {
      try {
        commit('SET_LOADING', true)
        const response = await adminService.unassignRequest(requestId)
        const updatedRequest = response.data
        commit('UPDATE_REQUEST', updatedRequest)
        return updatedRequest
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    }
  }
}
