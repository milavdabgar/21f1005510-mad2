import axios from 'axios';
import apiClient from './api'

// Add a request interceptor to add the auth token to requests
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle token expiration
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Base URL for API requests
const API_PORT = import.meta.env.VITE_API_PORT || '5000';
axios.defaults.baseURL = `http://localhost:${API_PORT}`;

// Helper function to handle API errors
const handleError = (error) => {
  let message = 'An error occurred. Please try again.';
  
  if (error.response) {
    message = error.response.data.message || error.response.data.error || message;
  } else if (error.request) {
    message = 'Server not responding. Please try again later.';
  }
  
  const customError = new Error(message);
  customError.response = error.response;
  throw customError;
};

// Helper function to create form data
const createFormData = (data) => {
  const formData = new FormData();
  
  // Add all non-file fields
  Object.entries(data).forEach(([key, value]) => {
    if (!['id_proof', 'certification'].includes(key)) {
      // Convert experience to string for FormData
      if (key === 'experience') {
        formData.append(key, value.toString());
      } else {
        formData.append(key, value);
      }
    }
  });
  
  // Add files if present
  if (data.id_proof) {
    formData.append('id_proof', data.id_proof);
  }
  if (data.certification) {
    formData.append('certification', data.certification);
  }
  
  return formData;
};

export const AuthService = {
  // User registration
  async register(userData) {
    try {
      const formData = createFormData(userData);
      
      // Set proper headers for multipart/form-data
      const config = {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      };
      
      const response = await apiClient.post('/auth/register', formData, config);
      return response.data;
    } catch (error) {
      console.error('Registration Error:', error);
      throw error;
    }
  },

  // User login
  async login(credentials) {
    try {
      console.log('Login Attempt:', { email: credentials.email });
      const response = await apiClient.post('/auth/login', credentials);
      return response.data;
    } catch (error) {
      console.error('Login Error:', error);
      throw error;
    }
  },

  // Get user profile
  async getProfile() {
    try {
      // First get the basic user info
      const response = await apiClient.get('/auth/profile');
      const userData = response.data.user;

      // If user is customer or professional, get additional info from type-specific endpoint
      if (userData.type === 'customer') {
        try {
          const customerResponse = await apiClient.get('/customers/profile');
          return {
            user: {
              ...userData,
              ...customerResponse.data.user,
              address: customerResponse.data.address,
              pincode: customerResponse.data.pincode
            }
          };
        } catch (error) {
          console.error('Failed to fetch customer profile:', error);
          return { user: userData }; // Return basic user data if customer profile fails
        }
      } else if (userData.type === 'professional') {
        try {
          const professionalResponse = await apiClient.get('/professionals/profile');
          return {
            user: {
              ...userData,
              ...professionalResponse.data.user,
              experience: professionalResponse.data.experience,
              service_type: professionalResponse.data.service_type,
              charges: professionalResponse.data.charges
            }
          };
        } catch (error) {
          console.error('Failed to fetch professional profile:', error);
          return { user: userData }; // Return basic user data if professional profile fails
        }
      }

      return { user: userData };
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      throw error;
    }
  },

  // Update user profile
  async updateProfile(profileData) {
    try {
      // Get current user type
      const currentUser = (await apiClient.get('/auth/profile')).data;
      
      // Update basic info through auth endpoint
      const basicData = {
        name: profileData.name,
        phone: profileData.phone
      };
      await apiClient.put('/auth/profile', basicData);

      // Update type-specific info through respective endpoints
      if (currentUser.type === 'customer') {
        const customerData = {
          address: profileData.address,
          pincode: profileData.pincode
        };
        await apiClient.put('/customers/profile', customerData);
      } else if (currentUser.type === 'professional') {
        const professionalData = {
          experience: profileData.experience,
          service_type: profileData.service_type,
          charges: profileData.charges,
          available: profileData.available
        };
        await apiClient.put('/professionals/profile', professionalData);
      }

      // Get and return updated profile
      return await this.getProfile();
    } catch (error) {
      handleError(error);
    }
  },

  // Admin: List professionals
  async listProfessionals() {
    const response = await apiClient.get('/api/auth/professionals');
    return response.data;
  },

  // Admin: Approve professional
  async approveProfessional(professionalId) {
    const response = await apiClient.post(`/api/auth/professionals/${professionalId}/approve`);
    return response.data;
  },

  // Admin: Reject professional
  async rejectProfessional(professionalId, reason) {
    const response = await apiClient.post(`/api/auth/professionals/${professionalId}/reject`, { reason });
    return response.data;
  },

  // Admin: Block user
  async blockUser(userId, reason) {
    const response = await apiClient.post(`/api/auth/users/${userId}/block`, { reason });
    return response.data;
  },

  // Admin: Unblock user
  async unblockUser(userId) {
    const response = await apiClient.post(`/api/auth/users/${userId}/unblock`);
    return response.data;
  },

  // Admin: Search users
  async searchUsers(query) {
    const response = await apiClient.get('/api/auth/users/search', { params: query });
    return response.data;
  },

  // List all professionals
  async listProfessionalsAdmin() {
    try {
      const response = await apiClient.get('/api/admin/professionals')
      return response.data
    } catch (error) {
      throw handleError(error)
    }
  },

  // Get professional details
  async getProfessionalDetails(id) {
    try {
      const response = await apiClient.get(`/api/admin/professionals/${id}`)
      return response.data
    } catch (error) {
      throw handleError(error)
    }
  },

  // Approve professional
  async approveProfessionalAdmin(id) {
    try {
      const response = await apiClient.post(`/api/admin/professionals/${id}/approve`)
      return response.data
    } catch (error) {
      throw handleError(error)
    }
  },

  // Reject professional
  async rejectProfessionalAdmin(id, reason) {
    try {
      const response = await apiClient.post(`/api/admin/professionals/${id}/reject`, { reason })
      return response.data
    } catch (error) {
      throw handleError(error)
    }
  },

  // Block professional
  async blockProfessional(id, reason) {
    try {
      const response = await apiClient.post(`/api/admin/professionals/${id}/block`, { reason })
      return response.data
    } catch (error) {
      throw handleError(error)
    }
  },

  // Get professional documents
  async getProfessionalDocuments(id) {
    try {
      const response = await apiClient.get(`/api/admin/professionals/${id}/documents`)
      return response.data
    } catch (error) {
      throw handleError(error)
    }
  }
};
