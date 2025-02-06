<template>
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
          <!-- Common fields for all users -->
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

          <!-- Customer specific fields -->
          <template v-if="isCustomer">
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
          </template>

          <!-- Professional specific fields -->
          <template v-if="isProfessional">
            <div class="mb-3">
              <label for="experience" class="form-label">Experience</label>
              <input
                type="text"
                class="form-control"
                id="experience"
                v-model="formData.experience"
                required
              />
            </div>

            <div class="mb-3">
              <label for="service_type" class="form-label">Service Type</label>
              <input
                type="text"
                class="form-control"
                id="service_type"
                v-model="formData.service_type"
                required
              />
            </div>

            <div class="mb-3">
              <label for="charges" class="form-label">Charges (per hour)</label>
              <input
                type="number"
                class="form-control"
                id="charges"
                v-model="formData.charges"
                required
              />
            </div>
          </template>

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
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
  name: 'ProfileForm',
  
  data() {
    return {
      formData: {
        email: '',
        name: '',
        phone: '',
        // Customer fields
        address: '',
        pincode: '',
        // Professional fields
        experience: '',
        service_type: '',
        charges: null
      },
      success: '',
      error: '',
      loading: false
    };
  },

  computed: {
    ...mapGetters('auth', [
      'currentUser',
      'isCustomer',
      'isProfessional',
      'isAdmin'
    ])
  },

  methods: {
    ...mapActions('auth', ['updateProfile']),

    async handleSubmit() {
      this.loading = true;
      this.error = '';
      this.success = '';

      try {
        const profileData = { ...this.formData };
        
        // Remove irrelevant fields based on user type
        if (!this.isCustomer) {
          delete profileData.address;
          delete profileData.pincode;
        }
        if (!this.isProfessional) {
          delete profileData.experience;
          delete profileData.service_type;
          delete profileData.charges;
        }

        await this.updateProfile(profileData);
        this.success = 'Profile updated successfully!';
      } catch (error) {
        this.error = error.response?.data?.message || 'Failed to update profile';
      } finally {
        this.loading = false;
      }
    },

    initializeForm() {
      if (this.currentUser) {
        // Set common fields
        this.formData.email = this.currentUser.email;
        this.formData.name = this.currentUser.name || '';
        this.formData.phone = this.currentUser.phone || '';

        // Set customer specific fields
        if (this.isCustomer) {
          this.formData.address = this.currentUser.address || '';
          this.formData.pincode = this.currentUser.pincode || '';
        }

        // Set professional specific fields
        if (this.isProfessional) {
          this.formData.experience = this.currentUser.experience || '';
          this.formData.service_type = this.currentUser.service_type || '';
          this.formData.charges = this.currentUser.charges || '';
        }
      }
    }
  },

  mounted() {
    this.initializeForm();
  },

  watch: {
    currentUser: {
      handler() {
        this.initializeForm();
      },
      deep: true
    }
  }
};
</script>

<style scoped>
.profile-form {
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.card {
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}
</style>
