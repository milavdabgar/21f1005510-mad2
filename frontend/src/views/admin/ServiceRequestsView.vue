<template>
  <div class="container mx-auto px-4 py-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold mb-6">Service Requests</h1>
    </div>

    <!-- Search and Filter -->
    <div class="filters">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="Search requests..." 
        class="form-control"
      >
      <select 
        v-model="selectedStatus" 
        class="form-control"
      >
        <option value="">All Status</option>
        <option value="requested">Requested</option>
        <option value="assigned">Assigned</option>
        <option value="approved">Accepted</option>
        <option value="rejected">Rejected</option>
        <option value="completed">Completed</option>
        <option value="closed">Closed</option>
        
      </select>
    </div>

    <!-- Service Requests Table -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th @click="sort('id')" :class="getSortClass('id')">ID</th>
            <th @click="sort('service')" :class="getSortClass('service')">Service</th>
            <th @click="sort('customer')" :class="getSortClass('customer')">Customer</th>
            <th @click="sort('professional')" :class="getSortClass('professional')">Professional</th>
            <th @click="sort('request_date')" :class="getSortClass('request_date')">Requested Date</th>
            <th @click="sort('status')" :class="getSortClass('status')">Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="request in filteredRequests" :key="request.id">
            <td class="clickable" @click="viewDetails(request)">{{ request.id }}</td>
            <td class="clickable" @click="viewDetails(request)">{{ request.service?.name || request.remarks }}</td>
            <td>{{ request.customer?.name || 'Unknown Customer' }}</td>
            <td>{{ request.professional?.name || 'Not Assigned' }}</td>
            <td>{{ formatDate(request.request_date) }}</td>
            <td>
              <span class="status-badge" :class="'status-' + request.status.toLowerCase()">
                {{ request.status }}
              </span>
            </td>
            <td>
              <div class="action-buttons">
                <button 
                  @click="viewDetails(request)" 
                  class="btn-view"
                >
                  View
                </button>
                <button 
                  v-if="request.status === 'requested'"
                  @click="assignProfessional(request)" 
                  class="btn btn-sm btn-primary"
                >
                  Assign
                </button>
                <button 
                  v-if="request.status === 'rejected'"
                  @click="assignProfessional(request)" 
                  class="btn btn-sm btn-primary"
                >
                  Reassign
                </button>
                <button 
                  v-if="request.status === 'assigned'"
                  @click="unassignProfessional(request)" 
                  class="btn btn-sm btn-secondary"
                >
                  Unassign
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Assign Professional Modal -->
    <div v-if="showAssignModal" class="admin-modal">
      <div class="admin-modal__content">
        <div class="admin-modal__header">
          <h3 class="admin-modal__title">Assign Professional</h3>
          <button @click="showAssignModal = false" class="admin-modal__close">&times;</button>
        </div>
        <div class="admin-modal__body">
          <div class="form-group">
            <label class="form-label">Select Professional</label>
            <select v-model="selectedProfessionalId" class="form-control">
              <option value="">Select a professional</option>
              <option v-for="pro in availableProfessionals" :key="pro.id" :value="pro.id">
                {{ pro.name }} ({{ pro.service_type }})
              </option>
            </select>
          </div>
        </div>
        <div class="admin-modal__footer">
          <button @click="showAssignModal = false" class="btn btn-secondary">Cancel</button>
          <button @click="confirmAssign" class="btn btn-primary" :disabled="!selectedProfessionalId">
            Assign
          </button>
        </div>
      </div>
    </div>

    <!-- Service Request Details Modal -->
    <div v-if="showDetailsModal" class="admin-modal">
      <div class="admin-modal__content">
        <div class="admin-modal__header">
          <h3 class="admin-modal__title">Service Request Details</h3>
          <button @click="closeModal" class="admin-modal__close">&times;</button>
        </div>
        <div class="admin-modal__body">
          <div class="row mb-3">
            <div class="col-4">Service</div>
            <div class="col-8">{{ selectedRequest.service?.name || selectedRequest.remarks }}</div>
          </div>
          <div class="row mb-3">
            <div class="col-4">Customer</div>
            <div class="col-8">{{ selectedRequest.customer?.name || 'Unknown Customer' }}</div>
          </div>
          <div class="row mb-3">
            <div class="col-4">Address</div>
            <div class="col-8">{{ selectedRequest.customer?.address }}{{ selectedRequest.customer?.pincode ? `, ${selectedRequest.customer.pincode}` : '' }}</div>
          </div>
          <div class="row mb-3">
            <div class="col-4">Professional</div>
            <div class="col-8">{{ selectedRequest.professional?.name || 'Not Assigned' }}</div>
          </div>
          <div class="row mb-3">
            <div class="col-4">Status</div>
            <div class="col-8">
              <span class="status-badge" :class="'status-' + selectedRequest.status.toLowerCase()">
                {{ selectedRequest.status }}
              </span>
            </div>
          </div>
          <div class="row mb-3">
            <div class="col-4">Date</div>
            <div class="col-8">{{ formatDate(selectedRequest.created_at || selectedRequest.request_date) }}</div>
          </div>
          <div v-if="['completed', 'closed'].includes(selectedRequest.status)" class="row mb-3">
            <div class="col-4">Rating</div>
            <div class="col-8">
              <div class="star-rating">
                <span v-if="selectedRequest.rating">
                  {{ '★'.repeat(selectedRequest.rating) }}{{ '☆'.repeat(5 - selectedRequest.rating) }}
                </span>
                <span v-else>Not rated</span>
              </div>
            </div>
          </div>
          <div v-if="selectedRequest.remarks" class="row mb-3">
            <div class="col-4">Remarks</div>
            <div class="col-8">{{ selectedRequest.remarks }}</div>
          </div>
        </div>
        <div class="admin-modal__footer">
          <button @click="closeModal" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'

export default {
  name: 'ServiceRequestsView',
  data() {
    return {
      searchQuery: '',
      selectedStatus: '',
      showDetailsModal: false,
      showAssignModal: false,
      selectedRequest: null,
      selectedProfessionalId: '',
      currentRequest: null,
      sortKey: 'id',
      sortOrder: 'asc'
    }
  },

  computed: {
    ...mapState('admin', ['serviceRequests', 'professionals', 'loading', 'error']),
    filteredRequests() {
      if (!this.serviceRequests) return []
      
      return this.serviceRequests.filter(request => {
        if (!request) return false
        
        const searchLower = this.searchQuery.toLowerCase()
        const customerName = request.customer?.name || ''
        const professionalName = request.professional?.name || ''
        const serviceName = request.service?.name || request.remarks || ''
        
        return (
          customerName.toLowerCase().includes(searchLower) ||
          professionalName.toLowerCase().includes(searchLower) ||
          serviceName.toLowerCase().includes(searchLower)
        ) && (
          this.selectedStatus === '' || request.status === this.selectedStatus
        )
      }).sort((a, b) => {
        if (this.sortKey === 'id') {
          return this.sortOrder === 'asc' ? a.id - b.id : b.id - a.id
        } else if (this.sortKey === 'service') {
          return this.sortOrder === 'asc' ? a.service.name.localeCompare(b.service.name) : b.service.name.localeCompare(a.service.name)
        } else if (this.sortKey === 'customer') {
          return this.sortOrder === 'asc' ? a.customer.name.localeCompare(b.customer.name) : b.customer.name.localeCompare(a.customer.name)
        } else if (this.sortKey === 'professional') {
          return this.sortOrder === 'asc' ? a.professional.name.localeCompare(b.professional.name) : b.professional.name.localeCompare(a.professional.name)
        } else if (this.sortKey === 'request_date') {
          return this.sortOrder === 'asc' ? new Date(a.request_date) - new Date(b.request_date) : new Date(b.request_date) - new Date(a.request_date)
        } else if (this.sortKey === 'status') {
          return this.sortOrder === 'asc' ? a.status.localeCompare(b.status) : b.status.localeCompare(a.status)
        }
      })
    },
    availableProfessionals() {
      if (!this.currentRequest?.service?.type) return []
      
      // Convert types to lowercase for case-insensitive comparison
      const requestType = this.currentRequest.service.type.toLowerCase()
      console.log('Current request:', this.currentRequest)
      console.log('All professionals:', this.professionals)
      console.log('Request type:', requestType)
      
      const filtered = this.professionals.filter(p => {
        console.log('Checking professional:', p)
        console.log('Status match:', p.status === 'approved')
        console.log('Active match:', p.active)
        console.log('Available match:', p.available)
        console.log('Service type match:', p.service_type?.toLowerCase() === requestType)
        return p.status === 'approved' && 
               p.active && 
               p.available &&
               p.service_type?.toLowerCase() === requestType
      })
      
      console.log('Filtered professionals:', filtered)
      return filtered
    }
  },

  watch: {
    searchQuery() {
      this.fetchServiceRequests({
        q: this.searchQuery,
        status: this.selectedStatus
      })
    },
    selectedStatus() {
      this.fetchServiceRequests({
        q: this.searchQuery,
        status: this.selectedStatus
      })
    }
  },

  methods: {
    ...mapActions('admin', [
      'fetchServiceRequests', 
      'fetchProfessionals', 
      'updateRequestStatus',
      'assignRequest',
      'unassignRequest'
    ]),

    async approveRequest(id) {
      try {
        await this.updateRequestStatus({ requestId: id, status: 'approved' })
        await this.fetchServiceRequests()
      } catch (error) {
        console.error('Error approving request:', error)
      }
    },

    async completeRequest(id) {
      try {
        await this.updateRequestStatus({ requestId: id, status: 'completed' })
        await this.fetchServiceRequests()
      } catch (error) {
        console.error('Error completing request:', error)
      }
    },

    async rejectRequest(id) {
      try {
        await this.updateRequestStatus({ requestId: id, status: 'rejected' })
        await this.fetchServiceRequests()
      } catch (error) {
        console.error('Error rejecting request:', error)
      }
    },

    assignProfessional(request) {
      this.currentRequest = request
      this.showAssignModal = true
      this.fetchProfessionals()
    },

    async confirmAssign() {
      try {
        await this.assignRequest({
          requestId: this.currentRequest.id,
          professionalId: this.selectedProfessionalId
        })
        this.showAssignModal = false
        this.selectedProfessionalId = null
        this.currentRequest = null
      } catch (error) {
        console.error('Failed to assign professional:', error)
      }
    },

    async unassignProfessional(request) {
      try {
        await this.unassignRequest(request.id)
      } catch (error) {
        console.error('Failed to unassign professional:', error)
      }
    },

    viewDetails(request) {
      this.selectedRequest = request
      this.showDetailsModal = true
    },

    closeModal() {
      this.showDetailsModal = false
      this.selectedRequest = null
    },

    formatDate(dateString) {
      if (!dateString) return 'Not available'
      const date = new Date(dateString)
      return date.toISOString().split('T')[0]
    },

    sort(key) {
      if (this.sortKey === key) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortKey = key
        this.sortOrder = 'asc'
      }
    },

    getSortClass(key) {
      return {
        'asc': this.sortKey === key && this.sortOrder === 'asc',
        'desc': this.sortKey === key && this.sortOrder === 'desc'
      }
    }
  },

  created() {
    this.fetchServiceRequests()
  }
}
</script>

<style scoped>
.request-notes {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
  white-space: pre-wrap;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-requested {
  background-color: #fef3c7;
  color: #92400e;
}

.status-assigned {
  background-color: #dbeafe;
  color: #1e40af;
}

.status-approved {
  background-color: #d1fae5;
  color: #065f46;
}

.status-rejected {
  background-color: #fee2e2;
  color: #991b1b;
}

.status-completed {
  background-color: #dcfce7;
  color: #166534;
}

.status-closed {
  background-color: #f3f4f6;
  color: #374151;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.btn-view {
  background-color: #6b7280;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
}

.btn-view:hover {
  background-color: #4b5563;
}

.star-rating {
  display: flex;
  align-items: center;
  font-size: 1.25rem;
}
</style>
