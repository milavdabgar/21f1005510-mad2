<template>
  <div class="profile-view">
    <div class="container">
      <div class="profile-form">
        <div class="card">
          <div class="card-body">
            <h2 class="text-center mb-4">Professional Profile</h2>
            
            <div v-if="error" class="alert alert-danger" role="alert">
              {{ error }}
            </div>
            
            <div v-if="success" class="alert alert-success" role="alert">
              {{ success }}
            </div>

            <form @submit.prevent="handleSubmit">
              <!-- Basic Info -->
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

              <!-- Professional Specific Info -->
              <div class="mb-3">
                <label for="service_type" class="form-label">Service Type</label>
                <input
                  type="text"
                  class="form-control"
                  id="service_type"
                  v-model="formData.service_type"
                  disabled
                />
              </div>

              <div class="mb-3">
                <label for="experience" class="form-label">Experience (years)</label>
                <input
                  type="number"
                  class="form-control"
                  id="experience"
                  v-model="formData.experience"
                  required
                />
              </div>

              <div class="mb-3">
                <div class="form-check form-switch">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    id="available"
                    v-model="formData.available"
                  />
                  <label class="form-check-label" for="available">Available for Service</label>
                </div>
              </div>

              <!-- Status Info -->
              <div class="mb-3">
                <label class="form-label">Status</label>
                <div class="alert" :class="statusClass" role="alert">
                  {{ formData.status }}
                </div>
              </div>

              <div v-if="formData.verified" class="mb-3">
                <div class="alert alert-success">
                  Verified on {{ new Date(formData.verified_at).toLocaleDateString() }}
                </div>
              </div>

              <div v-if="formData.rejection_reason" class="mb-3">
                <div class="alert alert-danger">
                  Rejection Reason: {{ formData.rejection_reason }}
                </div>
              </div>

              <button type="submit" class="btn btn-primary w-100" :disabled="!canUpdate">
                Update Profile
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import professionalService from '@/services/professional'

export default {
  name: 'ProfileView',
  setup() {
    const error = ref('')
    const success = ref('')
    const formData = ref({
      email: '',
      name: '',
      phone: '',
      experience: '',
      service_type: '',
      available: false,
      status: '',
      verified: false,
      verified_at: null,
      rejection_reason: ''
    })

    // Watch for changes in availability toggle
    watch(() => formData.value.available, async (newValue) => {
      try {
        await professionalService.updateAvailability(newValue)
        success.value = 'Availability updated successfully'
        setTimeout(() => success.value = '', 3000)
      } catch (err) {
        // Revert the toggle if the API call fails
        formData.value.available = !newValue
        error.value = err.message || 'Failed to update availability'
        setTimeout(() => error.value = '', 3000)
        console.error(err)
      }
    })

    const showError = (message) => {
      error.value = message
      setTimeout(() => error.value = '', 3000)
    }

    const showSuccess = (message) => {
      success.value = message
      setTimeout(() => success.value = '', 3000)
    }

    const statusClass = computed(() => {
      switch (formData.value.status) {
        case 'approved':
          return 'alert-success'
        case 'pending':
          return 'alert-warning'
        case 'rejected':
          return 'alert-danger'
        default:
          return 'alert-info'
      }
    })

    const canUpdate = computed(() => {
      return formData.value.status === 'approved' && formData.value.verified
    })

    const loadProfile = async () => {
      try {
        const response = await professionalService.getProfile()
        const { user, ...professionalData } = response
        formData.value = {
          ...user,
          ...professionalData
        }
      } catch (err) {
        showError('Failed to load profile')
        console.error(err)
      }
    }

    const handleSubmit = async () => {
      try {
        const updateData = {
          name: formData.value.name,
          phone: formData.value.phone,
          experience: formData.value.experience,
          available: formData.value.available
        }
        await professionalService.updateProfile(updateData)
        showSuccess('Profile updated successfully')
      } catch (err) {
        showError(err.message || 'Failed to update profile')
        console.error(err)
      }
    }

    onMounted(loadProfile)

    return {
      error,
      success,
      formData,
      statusClass,
      canUpdate,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.profile-view {
  padding: 20px 0;
}
.profile-form {
  max-width: 600px;
  margin: 0 auto;
}
</style>
