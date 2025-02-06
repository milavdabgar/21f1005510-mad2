import axios from 'axios'
import router from '../router'
import store from '../store'

// Base URL for API requests
const API_PORT = import.meta.env.VITE_API_PORT || '5000'
const API_URL = `http://localhost:${API_PORT}/api`

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  }
})

// Request interceptor
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    console.log('Request:', config.method.toUpperCase(), config.url, config.data)
    return config
  },
  error => {
    console.error('Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  response => {
    console.log('Response:', response.status, response.data)
    return response
  },
  error => {
    console.error('Response Error:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    })

    // Handle token expiration
    if (error.response?.status === 401) {
      store.commit('auth/clearAuth')
      if (router.currentRoute.value.meta.requiresAuth) {
        router.push('/login')
      }
    }

    // Format error message
    const message = error.response?.data?.message ||
                   error.response?.data?.error ||
                   error.message ||
                   'An error occurred'
    
    // Create a new error with the formatted message and attach the response
    const customError = new Error(message)
    customError.response = error.response
    return Promise.reject(customError)
  }
)

export default apiClient
