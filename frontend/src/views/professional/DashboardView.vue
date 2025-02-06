<template>
  <div class="dashboard-view">
    <div class="container">
      <div v-if="error" class="alert alert-danger" role="alert">
        {{ error }}
      </div>
      <div v-if="success" class="alert alert-success" role="alert">
        {{ success }}
      </div>

      <!-- New Service Requests Section -->
      <div class="card mb-4">
        <div class="card-header">
          <h3>New Service Requests</h3>
        </div>
        <div class="card-body">
          <div v-if="newRequests.length === 0" class="text-center">
            No new service requests
          </div>
          <div v-else class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Service</th>
                  <th>Customer</th>
                  <th>Address</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="request in newRequests" :key="request.id">
                  <td>{{ request.id }}</td>
                  <td>{{ request.service?.name }}</td>
                  <td>{{ request.customer?.name }}</td>
                  <td>{{ request.customer?.address }}{{ request.customer?.pincode ? `, ${request.customer.pincode}` : '' }}</td>
                  <td>
                    <div class="btn-group">
                      <button 
                        class="btn btn-success btn-sm"
                        @click="acceptRequest(request.id)"
                      >
                        Accept
                      </button>
                      <button 
                        class="btn btn-danger btn-sm"
                        @click="rejectRequest(request.id)"
                      >
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Active Service Requests Section -->
      <div class="card mb-4">
        <div class="card-header">
          <h3>Active Service Requests</h3>
        </div>
        <div class="card-body">
          <div v-if="activeRequests.length === 0" class="text-center">
            No active service requests
          </div>
          <div v-else class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Service</th>
                  <th>Customer</th>
                  <th>Address</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="request in activeRequests" :key="request.id">
                  <td>{{ request.id }}</td>
                  <td>{{ request.service?.name }}</td>
                  <td>{{ request.customer?.name }}</td>
                  <td>{{ request.customer?.address }}{{ request.customer?.pincode ? `, ${request.customer.pincode}` : '' }}</td>
                  <td>
                    <span class="badge bg-primary">{{ request.status }}</span>
                  </td>
                  <td>
                    <button 
                      class="btn btn-success btn-sm"
                      @click="completeRequest(request.id)"
                    >
                      Mark Complete
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Service Request History Section -->
      <div class="card">
        <div class="card-header">
          <h3>Service Request History</h3>
        </div>
        <div class="card-body">
          <div v-if="completedRequests.length === 0" class="text-center">
            No completed service requests
          </div>
          <div v-else class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Service</th>
                  <th>Customer</th>
                  <th>Address</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Rating</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="request in completedRequests" :key="request.id">
                  <td>{{ request.id }}</td>
                  <td>{{ request.service?.name }}</td>
                  <td>{{ request.customer?.name }}</td>
                  <td>{{ request.customer?.address }}{{ request.customer?.pincode ? `, ${request.customer.pincode}` : '' }}</td>
                  <td>
                    <span class="badge bg-success">completed</span>
                  </td>
                  <td>{{ formatDate(request.created_at || request.request_date) }}</td>
                  <td>
                    <span v-if="request.rating" class="rating">
                      {{ '★'.repeat(request.rating) }}{{ '☆'.repeat(5 - request.rating) }}
                    </span>
                    <span v-else>Not rated</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import professionalService from '@/services/professional'

export default {
  name: 'DashboardView',
  setup() {
    const error = ref('')
    const success = ref('')
    const newRequests = ref([])
    const activeRequests = ref([])
    const completedRequests = ref([])

    const showError = (message) => {
      error.value = message
      setTimeout(() => error.value = '', 3000)
    }

    const showSuccess = (message) => {
      success.value = message
      setTimeout(() => success.value = '', 3000)
    }

    const loadDashboard = async () => {
      try {
        console.log('Loading dashboard...')
        
        // Clear existing data first
        newRequests.value = []
        activeRequests.value = []
        completedRequests.value = []

        // Add cache-busting parameter
        const timestamp = new Date().getTime()
        
        // Fetch new requests (assigned only)
        console.log('Fetching new requests...')
        const newResponse = await professionalService.getRequests({ 
          status: 'new',
          _t: timestamp 
        })
        console.log('New response:', newResponse)
        newRequests.value = newResponse.items || []
        
        // Fetch active requests (accepted only)
        console.log('Fetching active requests...')
        const activeResponse = await professionalService.getRequests({ 
          status: 'active',
          _t: timestamp 
        })
        console.log('Active response:', activeResponse)
        activeRequests.value = activeResponse.items || []
        
        // Fetch completed requests (completed and closed)
        console.log('Fetching completed requests...')
        const completedResponse = await professionalService.getRequests({ 
          status: 'completed',
          _t: timestamp 
        })
        console.log('Completed response:', completedResponse)
        completedRequests.value = completedResponse.items || []

        console.log('Dashboard loaded:', {
          new: newRequests.value.length,
          active: activeRequests.value.length,
          completed: completedRequests.value.length
        })
      } catch (err) {
        showError('Failed to load dashboard')
        console.error('Dashboard load error:', err)
      }
    }

    const acceptRequest = async (requestId) => {
      try {
        await professionalService.acceptRequest(requestId)
        showSuccess('Request accepted successfully')
        await loadDashboard()
      } catch (err) {
        showError('Failed to accept request')
        console.error(err)
      }
    }

    const rejectRequest = async (requestId) => {
      try {
        await professionalService.rejectRequest(requestId)
        showSuccess('Request rejected successfully')
        await loadDashboard()
      } catch (err) {
        showError('Failed to reject request')
        console.error(err)
      }
    }

    const completeRequest = async (requestId) => {
      try {
        // Call API to complete request
        await professionalService.completeRequest(requestId)
        showSuccess('Request marked as completed successfully')

        // Remove from active requests immediately
        const completedRequest = activeRequests.value.find(r => r.id === requestId)
        activeRequests.value = activeRequests.value.filter(r => r.id !== requestId)
        
        if (completedRequest) {
          // Update request properties
          completedRequest.status = 'completed'
          completedRequest.completion_date = new Date().toISOString()
          
          // Add to completed requests
          completedRequests.value = [completedRequest, ...completedRequests.value]
        }

        // Refresh all lists to ensure consistency with backend
        await loadDashboard()

      } catch (err) {
        showError('Failed to complete request')
        console.error(err)
        // On error, refresh lists to ensure consistency
        await loadDashboard()
      }
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toISOString().split('T')[0]
    }

    let refreshInterval
    onMounted(() => {
      loadDashboard()
      refreshInterval = setInterval(loadDashboard, 30000)
    })
    
    onUnmounted(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    })

    return {
      error,
      success,
      newRequests,
      activeRequests,
      completedRequests,
      acceptRequest,
      rejectRequest,
      completeRequest,
      formatDate
    }
  }
}
</script>

<style scoped>
.dashboard-view {
  padding: 20px 0;
}

.card {
  margin-bottom: 20px;
}

.table {
  margin-bottom: 0;
}

.btn-group {
  gap: 5px;
}
</style>
