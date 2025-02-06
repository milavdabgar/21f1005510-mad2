// src/store/modules/customer.js
import { CustomerService } from '@/services/customer';

const state = {
  profile: null,
  services: [],
  categories: [],
  servicesPagination: null,
  requests: [],
  requestsPagination: null,
  dashboardStats: {},
  currentRequest: null,
  loading: false,
  error: null
};

const getters = {
  profile: state => state.profile,
  services: state => state.services,
  categories: state => state.categories,
  servicesPagination: state => state.servicesPagination,
  requests: state => state.requests,
  requestsPagination: state => state.requestsPagination,
  dashboardStats: state => state.dashboardStats,
  currentRequest: state => state.currentRequest,
  isLoading: state => state.loading,
  error: state => state.error
};

const mutations = {
  setProfile(state, profile) {
    state.profile = profile;
  },

  setServices(state, { items, pagination }) {
    state.services = items;
    state.servicesPagination = pagination;
  },

  setCategories(state, categories) {
    state.categories = categories;
  },

  setRequests(state, { items, pagination }) {
    state.requests = items;
    state.requestsPagination = pagination;
  },

  addRequest(state, request) {
    state.requests = [request, ...state.requests];
  },

  updateRequest(state, updatedRequest) {
    const index = state.requests.findIndex(r => r.id === updatedRequest.id);
    if (index !== -1) {
      state.requests.splice(index, 1, updatedRequest);
    }
  },

  setDashboardStats(state, stats) {
    state.dashboardStats = stats;
  },

  setLoading(state, loading) {
    state.loading = loading;
  },

  setError(state, error) {
    state.error = error;
  },

  clearError(state) {
    state.error = null;
  },

  setCurrentRequest(state, request) {
    state.currentRequest = request;
  }
};

const actions = {
  async fetchProfile({ commit }) {
    commit('setLoading', true);
    commit('clearError');

    try {
      const profile = await CustomerService.getProfile();
      commit('setProfile', profile);
      return profile;
    } catch (error) {
      commit('setError', error.message);
      throw error;
    } finally {
      commit('setLoading', false);
    }
  },

  async fetchServices({ commit }, params) {
    commit('setLoading', true);
    commit('clearError');

    try {
      const result = await CustomerService.getServices(params);
      commit('setServices', result);
      return result;
    } catch (error) {
      commit('setError', error.message);
      throw error;
    } finally {
      commit('setLoading', false);
    }
  },

  async fetchCategories({ commit }) {
    try {
      const response = await CustomerService.getCategories()
      commit('setCategories', response.items)
      return response.items
    } catch (error) {
      console.error('Error fetching categories:', error)
      throw error
    }
  },

  async fetchRequests({ commit }, params) {
    commit('setLoading', true);
    commit('clearError');

    try {
      const result = await CustomerService.getRequests(params);
      commit('setRequests', result);
      return result;
    } catch (error) {
      commit('setError', error.message);
      throw error;
    } finally {
      commit('setLoading', false);
    }
  },

  async createRequest({ commit }, requestData) {
    commit('setLoading', true);
    commit('clearError');

    try {
      const request = await CustomerService.createRequest(requestData);
      commit('addRequest', request);
      return request;
    } catch (error) {
      commit('setError', error.message);
      throw error;
    } finally {
      commit('setLoading', false);
    }
  },

  async cancelRequest({ commit }, requestId) {
    commit('setLoading', true);
    commit('clearError');

    try {
      const request = await CustomerService.cancelRequest(requestId);
      commit('updateRequest', request);
      return request;
    } catch (error) {
      commit('setError', error.message);
      throw error;
    } finally {
      commit('setLoading', false);
    }
  },

  async rateRequest({ commit }, { requestId, rating, remarks }) {
    commit('setLoading', true);
    commit('clearError');

    try {
      const request = await CustomerService.rateRequest(requestId, { rating, remarks });
      commit('updateRequest', request);
      return request;
    } catch (error) {
      commit('setError', error.message);
      throw error;
    } finally {
      commit('setLoading', false);
    }
  },

  async fetchDashboardStats({ commit }) {
    commit('setLoading', true);
    commit('clearError');

    try {
      const stats = await CustomerService.getDashboardStats();
      commit('setDashboardStats', stats);
      return stats;
    } catch (error) {
      commit('setError', error.message);
      throw error;
    } finally {
      commit('setLoading', false);
    }
  },

  async fetchRequestDetails({ commit }, requestId) {
    commit('setLoading', true);
    try {
      const response = await CustomerService.getRequestDetails(requestId);
      commit('setCurrentRequest', response);
      return response;
    } catch (error) {
      console.error('Error fetching request details:', error);
      throw error;
    } finally {
      commit('setLoading', false);
    }
  }
};

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
};
