// src/services/customer.js
import apiClient from './api';

export const CustomerService = {
  // Profile Management
  async getProfile() {
    try {
      const response = await apiClient.get('/customers/profile');
      return response.data;
    } catch (error) {
      console.error('Error fetching profile:', error);
      throw error;
    }
  },

  // Update customer profile
  async updateProfile(profileData) {
    try {
      const response = await apiClient.put('/customers/profile', {
        name: profileData.name,
        phone: profileData.phone,
        address: profileData.address,
        pincode: profileData.pincode
      });
      return response.data;
    } catch (error) {
      console.error('Error updating profile:', error);
      throw error;
    }
  },

  // Services
  async getServices(params = { page: 1, per_page: 10 }) {
    try {
      const response = await apiClient.get('/customers/services', { params });
      return {
        items: response.data.items,
        pagination: {
          total: response.data.total,
          current_page: response.data.current_page,
          per_page: response.data.per_page,
          pages: response.data.pages
        }
      };
    } catch (error) {
      console.error('Error fetching services:', error);
      throw error;
    }
  },

  async getCategories() {
    try {
      const response = await apiClient.get('/customers/services/categories');
      return response.data;
    } catch (error) {
      console.error('Error fetching categories:', error);
      throw error;
    }
  },

  // Service Requests
  async getRequests(params = { page: 1, per_page: 10 }) {
    try {
      const response = await apiClient.get('/customers/requests', { params });
      return {
        items: response.data.items,
        pagination: {
          total: response.data.total,
          current_page: response.data.current_page,
          per_page: response.data.per_page,
          pages: response.data.pages
        }
      };
    } catch (error) {
      console.error('Error fetching requests:', error);
      throw error;
    }
  },

  async createRequest(data) {
    try {
      const response = await apiClient.post('/customers/requests', data);
      return response.data;
    } catch (error) {
      console.error('Error creating request:', error);
      throw error;
    }
  },

  async cancelRequest(requestId) {
    try {
      const response = await apiClient.post(`/customers/requests/${requestId}/cancel`);
      return response.data;
    } catch (error) {
      console.error('Error canceling request:', error);
      throw error;
    }
  },

  async rateRequest(requestId, ratingData) {
    try {
      const response = await apiClient.post(`/customers/requests/${requestId}/rate`, {
        rating: ratingData.rating,
        remarks: ratingData.remarks || ''
      });
      return response.data;
    } catch (error) {
      console.error('Error rating request:', error);
      throw error;
    }
  },

  // Get request details
  async getRequestDetails(requestId) {
    try {
      const response = await apiClient.get(`/customers/requests/${requestId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching request details:', error);
      throw error;
    }
  },

  // Dashboard Stats
  async getDashboardStats() {
    try {
      const response = await apiClient.get('/customers/dashboard/stats');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      throw error;
    }
  }
};

export default CustomerService;
