<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>My Bookings</h2>
    </div>

    <!-- Search and Filters -->
    <div class="row g-3 mb-4">
      <div class="col-md-8">
        <input
          type="text"
          class="form-control"
          placeholder="Search by service name..."
          v-model="searchQuery"
        >
      </div>
      <div class="col-md-4">
        <select 
          class="form-select" 
          v-model="selectedStatus"
        >
          <option value="">All Status</option>
          <option value="requested">Requested</option>
          <option value="assigned">Assigned</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>
    </div>

    <!-- Requests List -->
    <div class="row">
      <div class="col-12">
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
            <div v-else-if="!sortedRequests.length" class="text-center py-4">
              <p class="mb-0">No bookings found</p>
              <router-link 
                :to="{ name: 'customer.services' }"
                class="btn btn-primary mt-3"
              >
                Browse Services
              </router-link>
            </div>
            <div v-else class="table-responsive">
              <table class="table table-hover">
                <thead>
                  <tr>
                    <th @click="sort('service')" class="cursor-pointer">
                      Service 
                      <i v-if="currentSort.key === 'service'" 
                         :class="['bi', currentSort.direction === 'asc' ? 'bi-arrow-up' : 'bi-arrow-down']">
                      </i>
                    </th>
                    <th @click="sort('professional')" class="cursor-pointer">
                      Professional
                      <i v-if="currentSort.key === 'professional'" 
                         :class="['bi', currentSort.direction === 'asc' ? 'bi-arrow-up' : 'bi-arrow-down']">
                      </i>
                    </th>
                    <th @click="sort('date')" class="cursor-pointer">
                      Date
                      <i v-if="currentSort.key === 'date'" 
                         :class="['bi', currentSort.direction === 'asc' ? 'bi-arrow-up' : 'bi-arrow-down']">
                      </i>
                    </th>
                    <th @click="sort('status')" class="cursor-pointer">
                      Status
                      <i v-if="currentSort.key === 'status'" 
                         :class="['bi', currentSort.direction === 'asc' ? 'bi-arrow-up' : 'bi-arrow-down']">
                      </i>
                    </th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="request in sortedRequests" :key="request.id">
                    <td>{{ request.service?.name || 'N/A' }}</td>
                    <td>{{ request.professional?.name || 'Pending' }}</td>
                    <td>{{ formatDate(request.request_date) }}</td>
                    <td>
                      <span :class="getStatusBadgeClass(request.status)">
                        {{ request.status }}
                      </span>
                    </td>
                    <td class="d-flex gap-2">
                      <button 
                        @click="viewRequest(request)" 
                        class="btn btn-sm btn-primary"
                      >
                        View
                      </button>
                      <button 
                        v-if="request.status === 'requested'"
                        @click="cancelRequest(request)" 
                        class="btn btn-sm btn-danger"
                      >
                        Cancel
                      </button>
                      <button 
                        v-if="['cancelled', 'closed'].includes(request.status)"
                        @click="bookAgain(request)" 
                        class="btn btn-sm btn-success"
                      >
                        Book Again
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

export default {
  name: 'RequestsView',
  setup() {
    const router = useRouter()
    const requests = ref([])
    const loading = ref(true)
    const error = ref(null)
    const searchQuery = ref('')
    const selectedStatus = ref('')
    const currentSort = ref({ key: 'date', direction: 'desc' })

    const fetchRequests = async () => {
      try {
        loading.value = true
        error.value = null
        const response = await axios.get('/api/customers/requests')
        console.log('Request data:', response.data)
        requests.value = response.data.items || []
        console.log('First request:', requests.value[0])
      } catch (err) {
        console.error('Error fetching requests:', err)
        error.value = 'Failed to load bookings. Please try again later.'
      } finally {
        loading.value = false
      }
    }

    const sort = (key) => {
      if (currentSort.value.key === key) {
        currentSort.value.direction = currentSort.value.direction === 'asc' ? 'desc' : 'asc'
      } else {
        currentSort.value = { key, direction: 'asc' }
      }
    }

    const filteredRequests = computed(() => {
      let result = [...requests.value]

      // Apply search filter
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        result = result.filter(request => 
          request.service?.name?.toLowerCase().includes(query) ||
          request.professional?.name?.toLowerCase().includes(query)
        )
      }

      // Apply status filter
      if (selectedStatus.value) {
        result = result.filter(request => request.status === selectedStatus.value)
      }

      return result
    })

    const sortedRequests = computed(() => {
      let result = [...filteredRequests.value]
      const { key, direction } = currentSort.value

      result.sort((a, b) => {
        let aVal, bVal

        switch (key) {
          case 'service':
            aVal = a.service?.name || ''
            bVal = b.service?.name || ''
            break
          case 'professional':
            aVal = a.professional?.name || ''
            bVal = b.professional?.name || ''
            break
          case 'date':
            return direction === 'asc' 
              ? new Date(a.request_date) - new Date(b.request_date)
              : new Date(b.request_date) - new Date(a.request_date)
          default:
            aVal = a[key] || ''
            bVal = b[key] || ''
        }

        if (direction === 'asc') {
          return aVal.localeCompare(bVal)
        } else {
          return bVal.localeCompare(aVal)
        }
      })

      return result
    })

    const viewRequest = (request) => {
      router.push({ 
        name: 'customer.request-details', 
        params: { id: request.id }
      })
    }

    const cancelRequest = async (request) => {
      try {
        await axios.post(`/api/customers/requests/${request.id}/cancel`)
        await fetchRequests()
      } catch (error) {
        console.error('Error canceling request:', error)
      }
    }

    const formatDate = (date) => {
      console.log('Formatting date:', date)
      if (!date) return 'N/A'
      return new Date(date).toLocaleString()
    }

    const getStatusBadgeClass = (status) => {
      const classes = {
        'REQUESTED': 'badge bg-secondary',
        'ASSIGNED': 'badge bg-primary',
        'IN_PROGRESS': 'badge bg-info',
        'COMPLETED': 'badge bg-success',
        'CANCELLED': 'badge bg-danger',
        'CLOSED': 'badge bg-dark'
      }
      return classes[status.toUpperCase()] || 'badge bg-secondary'
    }

    const bookAgain = (request) => {
      router.push({
        name: 'customer.services',
        query: { 
          type: request.service?.type,
          service: request.service?.id
        }
      })
    }

    onMounted(fetchRequests)

    return {
      sortedRequests,
      loading,
      error,
      searchQuery,
      selectedStatus,
      currentSort,
      formatDate,
      getStatusBadgeClass,
      sort,
      viewRequest,
      cancelRequest,
      bookAgain
    }
  }
}
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.cursor-pointer:hover {
  background-color: #f8f9fa;
}
.table th {
  font-weight: 600;
}
.badge {
  font-weight: 500;
  text-transform: capitalize;
}
.btn-primary {
  background-color: #0d6efd;
  border-color: #0d6efd;
}
.btn-primary:hover {
  background-color: #0b5ed7;
  border-color: #0a58ca;
}
.form-control, .form-select {
  border-radius: 0.375rem;
}
.table-responsive {
  border-radius: 0.375rem;
}
.d-flex.gap-2 {
  display: flex !important;
  gap: 0.5rem !important;
}
</style>
