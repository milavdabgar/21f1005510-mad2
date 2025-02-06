<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Book Service</h2>
      <button 
        @click="$router.back()"
        class="btn btn-outline-secondary"
      >
        Back
      </button>
    </div>

    <div class="row">
      <div class="col-md-8 mx-auto">
        <div class="card">
          <div class="card-body">
            <div v-if="loading" class="text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>
            <div v-else-if="error" class="text-center py-4 text-danger">
              {{ error }}
            </div>
            <div v-else>
              <!-- Service Details -->
              <div class="mb-4">
                <h4>{{ service.name }}</h4>
                <p class="text-muted">{{ service.description }}</p>
                <div class="d-flex gap-3 mb-3">
                  <span class="badge bg-primary">{{ service.type }}</span>
                  <span class="badge bg-info">₹{{ service.price }}</span>
                </div>
              </div>

              <!-- Booking Form -->
              <form @submit.prevent="submitBooking">
                <div class="mb-3">
                  <label for="remarks" class="form-label">Additional Notes</label>
                  <textarea
                    id="remarks"
                    v-model="remarks"
                    class="form-control"
                    rows="3"
                    placeholder="Any specific requirements or preferences..."
                  ></textarea>
                </div>

                <div class="d-grid">
                  <button 
                    type="submit" 
                    class="btn btn-primary"
                    :disabled="submitting"
                  >
                    <span v-if="submitting" class="spinner-border spinner-border-sm me-2" role="status"></span>
                    {{ submitting ? 'Booking...' : 'Confirm Booking' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'BookServiceView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const service = ref({})
    const remarks = ref('')
    const loading = ref(true)
    const submitting = ref(false)
    const error = ref(null)

    const fetchService = async () => {
      try {
        loading.value = true
        error.value = null
        const response = await axios.get(`/api/services/${route.params.id}`)
        service.value = response.data
      } catch (err) {
        console.error('Error fetching service:', err)
        error.value = 'Failed to load service details. Please try again later.'
      } finally {
        loading.value = false
      }
    }

    const submitBooking = async () => {
      try {
        submitting.value = true
        error.value = null

        await axios.post('/api/customers/requests', {
          service_id: parseInt(route.params.id),
          remarks: remarks.value
        })

        // Redirect to requests page after successful booking
        router.push({ 
          name: 'customer.requests',
          query: { success: 'true' }
        })
      } catch (err) {
        console.error('Error creating booking:', err)
        error.value = 'Failed to create booking. Please try again later.'
        submitting.value = false
      }
    }

    onMounted(() => {
      fetchService()
    })

    return {
      service,
      remarks,
      loading,
      submitting,
      error,
      submitBooking
    }
  }
}
</script>

<style scoped>
.badge {
  font-weight: 500;
}
</style>
