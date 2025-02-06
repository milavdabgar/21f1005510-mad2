import { AuthService } from '../../services/auth';
import { AUTH_MESSAGES } from '../../constants/messages';
import router from '../../router';

export default {
  namespaced: true,

  state: {
    token: localStorage.getItem('token') || null,
    user: null,
    loading: false,
    error: null
  },

  getters: {
    isAuthenticated: state => !!state.token,
    currentUser: state => state.user,
    userType: state => state.user?.type,
    isCustomer: state => state.user?.type === 'customer',
    isProfessional: state => state.user?.type === 'professional',
    isAdmin: state => state.user?.type === 'admin',
    loading: state => state.loading,
    isLoading: state => state.loading,
    error: state => state.error,
    authError: state => state.error
  },

  mutations: {
    setToken(state, token) {
      state.token = token;
      if (token) {
        localStorage.setItem('token', token);
      }
    },
    setUser(state, userData) {
      state.user = userData.user || userData;
      console.log('User set in store:', state.user);
    },
    clearAuth(state) {
      state.token = null;
      state.user = null;
      localStorage.removeItem('token');
    },
    setLoading(state, loading) {
      state.loading = loading;
    },
    setError(state, error) {
      state.error = error;
    },
    clearError(state) {
      state.error = null;
    }
  },

  actions: {
    async initialize({ commit, dispatch, state }) {
      // If we already have a user, no need to initialize
      if (state.user) {
        return;
      }

      // Check if we have a token
      const token = localStorage.getItem('token');
      if (!token) {
        commit('clearAuth');
        return;
      }

      try {
        // Set token in state
        commit('setToken', token);
        // Try to fetch user profile
        const response = await AuthService.getProfile();
        commit('setUser', response);
      } catch (error) {
        console.error('Failed to initialize auth state:', error);
        // If profile fetch fails, clear everything
        commit('clearAuth');
        throw error;
      }
    },

    async register({ commit }, userData) {
      try {
        commit('setLoading', true);
        commit('clearError');
        console.log('Registration Attempt:', userData);
        const response = await AuthService.register(userData);
        console.log('Registration response:', response);
        
        if (userData.type === 'customer') {
          // If customer, automatically log them in
          commit('setToken', response.access_token);
          commit('setUser', response);
        }
        
        return response;
      } catch (error) {
        commit('setError', error.message || AUTH_MESSAGES.REGISTER_ERROR);
        throw error;
      } finally {
        commit('setLoading', false);
      }
    },

    async login({ commit, dispatch }, credentials) {
      try {
        commit('setLoading', true);
        commit('clearError');
        console.log('Login Attempt:', credentials);
        const response = await AuthService.login(credentials);
        console.log('Login response:', response);
        
        commit('setToken', response.access_token);
        commit('setUser', response);
        
        // Determine redirect based on user type
        const userType = response.user?.type;
        let redirectPath = '/dashboard';
        
        if (userType === 'customer') {
          redirectPath = '/customer/dashboard';
        } else if (userType === 'professional') {
          redirectPath = '/professional/dashboard';
        }
        
        router.push(redirectPath);
        return response;
      } catch (error) {
        commit('setError', error.message || AUTH_MESSAGES.LOGIN_ERROR);
        throw error;
      } finally {
        commit('setLoading', false);
      }
    },

    async fetchProfile({ commit }) {
      try {
        const response = await AuthService.getProfile();
        console.log('Profile fetched:', response);
        commit('setUser', response);
        
        // Determine redirect based on user type if needed
        const userType = response.user?.type;
        if (router.currentRoute.value.path === '/') {
          if (userType === 'professional') {
            router.push('/professional/dashboard');
          } else if (userType === 'customer') {
            router.push('/customer/dashboard');
          } else if (userType === 'admin') {
            router.push('/admin');
          }
        }
        
        return response;
      } catch (error) {
        console.error('Error fetching profile:', error);
        commit('clearAuth');
        router.push('/login');
        throw error;
      }
    },

    async logout({ commit }) {
      commit('clearAuth');
      router.push('/login');
    }
  }
};
