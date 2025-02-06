import professionalService from '@/services/professional'

const state = {
  profile: null,
  requests: [],
  currentService: null,
  ratingsDistribution: [],
  stats: {
    completed: 0,
    closed: 0,
    rejected: 0,
    total: 0
  },
  loading: false,
  error: null
}

const getters = {
  profile: state => state.profile,
  requests: state => state.requests,
  currentService: state => state.currentService,
  ratingsDistribution: state => state.ratingsDistribution,
  stats: state => state.stats,
  isLoading: state => state.loading,
  error: state => state.error
}

const mutations = {
  setProfile(state, profile) {
    state.profile = profile
  },

  setRequests(state, requests) {
    state.requests = requests
  },

  setCurrentService(state, service) {
    state.currentService = service
  },

  setRatingsDistribution(state, distribution) {
    state.ratingsDistribution = distribution
  },

  setStats(state, stats) {
    state.stats = stats
  },

  setLoading(state, loading) {
    state.loading = loading
  },

  setError(state, error) {
    state.error = error
  },

  clearError(state) {
    state.error = null
  }
}

const actions = {
  async fetchProfile({ commit }) {
    try {
      commit('setLoading', true)
      const profile = await professionalService.getProfile()
      commit('setProfile', profile)
    } catch (error) {
      commit('setError', error.message)
      throw error
    } finally {
      commit('setLoading', false)
    }
  },

  async updateProfile({ commit }, profileData) {
    try {
      commit('setLoading', true)
      const profile = await professionalService.updateProfile(profileData)
      commit('setProfile', profile)
    } catch (error) {
      commit('setError', error.message)
      throw error
    } finally {
      commit('setLoading', false)
    }
  },

  async fetchRequests({ commit }) {
    try {
      commit('setLoading', true)
      const requests = await professionalService.getRequests()
      commit('setRequests', requests)
      
      // Update current service
      const currentService = requests.find(r => r.status === 'in_progress')
      commit('setCurrentService', currentService || null)

      // Calculate stats
      const stats = requests.reduce((acc, req) => {
        acc.total++
        if (req.status === 'completed') acc.completed++
        if (req.status === 'closed') acc.closed++
        if (req.status === 'rejected') acc.rejected++
        return acc
      }, { completed: 0, closed: 0, rejected: 0, total: 0 })
      commit('setStats', stats)

      // Calculate ratings distribution
      const ratings = requests.filter(req => req.rating).map(req => req.rating)
      const distribution = [5, 4, 3, 2, 1].map(stars => {
        const count = ratings.filter(r => r === stars).length
        return {
          stars,
          count,
          percentage: ratings.length ? (count / ratings.length) * 100 : 0
        }
      })
      commit('setRatingsDistribution', distribution)
    } catch (error) {
      commit('setError', error.message)
      throw error
    } finally {
      commit('setLoading', false)
    }
  },

  async acceptRequest({ dispatch }, requestId) {
    try {
      commit('setLoading', true)
      await professionalService.acceptRequest(requestId)
      await dispatch('fetchRequests')
    } catch (error) {
      commit('setError', error.message)
      throw error
    } finally {
      commit('setLoading', false)
    }
  },

  async rejectRequest({ dispatch }, requestId) {
    try {
      commit('setLoading', true)
      await professionalService.rejectRequest(requestId)
      await dispatch('fetchRequests')
    } catch (error) {
      commit('setError', error.message)
      throw error
    } finally {
      commit('setLoading', false)
    }
  },

  async completeRequest({ dispatch }, requestId) {
    try {
      commit('setLoading', true)
      await professionalService.completeRequest(requestId)
      await dispatch('fetchRequests')
    } catch (error) {
      commit('setError', error.message)
      throw error
    } finally {
      commit('setLoading', false)
    }
  },

  async updateAvailability({ commit }, available) {
    try {
      commit('setLoading', true)
      await professionalService.updateAvailability(available)
      await dispatch('fetchProfile')
    } catch (error) {
      commit('setError', error.message)
      throw error
    } finally {
      commit('setLoading', false)
    }
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
