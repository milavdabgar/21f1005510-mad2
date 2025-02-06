<template>
  <div class="profile-view">
    <div class="container">
      <div class="profile-form">
        <div class="card">
          <div class="card-body">
            <h2 class="text-center mb-4">Profile</h2>
            
            <div v-if="error" class="alert alert-danger" role="alert">
              {{ error }}
            </div>
            
            <div v-if="success" class="alert alert-success" role="alert">
              {{ success }}
            </div>

            <form @submit.prevent="handleSubmit">
              <div class="mb-3">
                <label for="email" class="form-label">Email</label>
                <input
                  type="email"
                  class="form-control"
                  id="email"
                  v-model="formData.email"
                  disabled
                />
              </div>

              <div class="mb-3">
                <label for="name" class="form-label">Name</label>
                <input
                  type="text"
                  class="form-control"
                  id="name"
                  v-model="formData.name"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="phone" class="form-label">Phone</label>
                <input
                  type="tel"
                  class="form-control"
                  id="phone"
                  v-model="formData.phone"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="address" class="form-label">Address</label>
                <textarea
                  class="form-control"
                  id="address"
                  v-model="formData.address"
                  required
                  rows="3"
                ></textarea>
              </div>

              <div class="mb-3">
                <label for="pincode" class="form-label">Pincode</label>
                <input
                  type="text"
                  class="form-control"
                  id="pincode"
                  v-model="formData.pincode"
                  required
                />
              </div>

              <button
                type="submit"
                class="btn btn-primary w-100"
                :disabled="loading"
              >
                {{ loading ? 'Saving...' : 'Save Changes' }}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { CustomerService } from '@/services/customer';

export default {
  name: 'CustomerProfileView',
  
  data() {
    return {
      formData: {
        email: '',
        name: '',
        phone: '',
        address: '',
        pincode: ''
      },
      loading: false,
      error: '',
      success: ''
    };
  },

  async mounted() {
    try {
      const response = await CustomerService.getProfile();
      const { user, address, pincode } = response;
      this.formData = {
        email: user.email,
        name: user.name || '',
        phone: user.phone || '',
        address: address || '',
        pincode: pincode || ''
      };
    } catch (error) {
      this.error = 'Failed to load profile data';
      console.error('Error loading profile:', error);
    }
  },

  methods: {
    async handleSubmit() {
      this.loading = true;
      this.error = '';
      this.success = '';

      try {
        // Only send updatable fields
        const updateData = {
          name: this.formData.name,
          phone: this.formData.phone,
          address: this.formData.address,
          pincode: this.formData.pincode
        };
        
        await CustomerService.updateProfile(updateData);
        this.success = 'Profile updated successfully!';
      } catch (error) {
        this.error = error.message || 'Failed to update profile';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.profile-view {
  min-height: calc(100vh - var(--navbar-height));
  padding: 2rem 0;
}

.profile-form {
  max-width: 600px;
  margin: 0 auto;
}

.card {
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}
</style>
