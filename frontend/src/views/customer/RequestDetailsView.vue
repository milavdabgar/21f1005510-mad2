// src/views/customer/RequestDetailsView.vue
<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Request #{{ request?.id }}</h2>
      <button 
        @click="$router.push('/customer/dashboard')"
        class="btn btn-outline-secondary"
      >
        Back to Dashboard
      </button>
    </div>

    <div v-if="loading" class="text-center py-4">
      Loading...
    </div>

    <div v-else-if="request" class="row">
      <!-- Request Details -->
      <div class="col-md-8">
        <div class="card p-4 mb-4">
          <h3 class="mb-3">Service Details</h3>
          <div class="service-info">
            <div class="row mb-3">
              <div class="col-md-4 fw-bold">Service:</div>
              <div class="col-md-8">{{ request.service.name }}</div>
            </div>
            <div class="row mb-3">
              <div class="col-md-4 fw-bold">Status:</div>
              <div class="col-md-8">
                <request-status :status="request.status" />
              </div>
            </div>
            <div class="row mb-3">
              <div class="col-md-4 fw-bold">Request Date:</div>
              <div class="col-md-8">{{ formatDate(request.request_date) }}</div>
            </div>
            <div class="row mb-3">
              <div class="col-md-4 fw-bold">Price:</div>
              <div class="col-md-8">₹{{ request.service.price }}</div>
            </div>
            <div class="row mb-3">
              <div class="col-md-4 fw-bold">Remarks:</div>
              <div class="col-md-8">{{ request.remarks || 'No remarks' }}</div>
            </div>
          </div>
        </div>

        <!-- Professional Details if assigned -->
        <div v-if="request.professional" class="card p-4 mb-4">
          <h3 class="mb-3">Professional Details</h3>
          <div class="professional-info">
            <div class="row mb-3">
              <div class="col-md-4 fw-bold">Name:</div>
              <div class="col-md-8">{{ request.professional.name }}</div>
            </div>
            <div class="row mb-3">
              <div class="col-md-4 fw-bold">Phone:</div>
              <div class="col-md-8">{{ request.professional.phone }}</div>
            </div>
            <div class="row mb-3">
              <div class="col-md-4 fw-bold">Experience:</div>
              <div class="col-md-8">{{ request.professional.experience }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions Sidebar -->
      <div class="col-md-4">
        <div class="card p-4">
          <h3 class="mb-3">Actions</h3>
          
          <!-- Available actions based on status -->
          <div class="d-grid gap-2">
            <button 
              v-if="canCancel"
              @click="cancelRequest"
              class="btn btn-danger"
            >
              Cancel Request
            </button>

            <button 
              v-if="request.status === 'completed'"
              @click="showRatingModal = true"
              class="btn btn-primary"
            >
              Rate Service
            </button>

            <button 
              v-if="request.rating"
              @click="showRatingModal = true"
              class="btn btn-outline-secondary"
            >
              View Rating
            </button>

            <button 
              v-if="request.status === 'completed'"
              @click="bookAgain"
              class="btn btn-outline-primary"
            >
              Book Again
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Rating Modal -->
    <rating-modal
      v-if="showRatingModal"
      :requestId="request.id"
      :readOnly="!!request.rating"
      :initialRating="request.rating || 0"
      :initialRemarks="request.rating_remarks || ''"
      @close="showRatingModal = false"
      @rated="handleRated"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CustomerService } from '@/services/customer'
import RequestStatus from '@/views/customer/components/RequestStatus.vue'
import RatingModal from '@/views/customer/components/RatingModal.vue'

const route = useRoute()
const router = useRouter()

const request = ref(null)
const loading = ref(true)
const error = ref(null)
const showRatingModal = ref(false)

// Computed properties
const canCancel = computed(() => {
  return request.value && ['requested', 'assigned'].includes(request.value.status)
})

// Methods
const loadRequest = async () => {
  loading.value = true
  error.value = null
  try {
    const requestId = parseInt(route.params.id)
    const data = await CustomerService.getRequestDetails(requestId)
    request.value = data
  } catch (err) {
    error.value = err.message || 'Failed to load request details'
  } finally {
    loading.value = false
  }
}

const cancelRequest = async () => {
  if (!confirm('Are you sure you want to cancel this request?')) return
  
  try {
    await CustomerService.cancelRequest(request.value.id)
    await loadRequest()
  } catch (err) {
    error.value = err.message || 'Failed to cancel request'
  }
}

const handleRated = async () => {
  await loadRequest()
  showRatingModal.value = false
}

const formatDate = (date) => {
  return new Date(date).toLocaleString()
}

const bookAgain = () => {
  router.push(`/customer/services/${request.value.service.type}`)
}

// Lifecycle hooks
onMounted(loadRequest)
</script>