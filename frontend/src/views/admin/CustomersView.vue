<template>
  <div class="container mx-auto px-4 py-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold mb-6">Customers</h1>
    </div>

    <!-- Search and Filter -->
    <div class="filters">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="Search customers..." 
        class="form-control"
      >
      <select 
        v-model="selectedStatus" 
        class="form-control"
      >
        <option value="">All Status</option>
        <option value="active">Active</option>
        <option value="blocked">Blocked</option>
      </select>
    </div>

    <!-- Customers Table -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th @click="sort('id')" :class="getSortClass('id')">ID</th>
            <th @click="sort('name')" :class="getSortClass('name')">Name</th>
            <th @click="sort('email')" :class="getSortClass('email')">Email</th>
            <th @click="sort('phone')" :class="getSortClass('phone')">Phone</th>
            <th @click="sort('status')" :class="getSortClass('status')">Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="customer in filteredCustomers" :key="customer.id">
            <td class="clickable" @click="viewDetails(customer)">{{ customer.id }}</td>
            <td class="clickable" @click="viewDetails(customer)">{{ customer.name }}</td>
            <td>{{ customer.email }}</td>
            <td>{{ customer.phone }}</td>
            <td>
              <span class="status-badge" :class="'status-' + customer.status.toLowerCase()">
                {{ customer.status }}
              </span>
            </td>
            <td>
              <div class="action-buttons">
                <button 
                  v-if="customer.active"
                  @click="blockCustomer(customer)" 
                  class="btn btn-sm btn-danger"
                >
                  Block
                </button>
                <button 
                  v-if="!customer.active"
                  @click="unblockCustomer(customer)" 
                  class="btn btn-sm btn-success"
                >
                  Unblock
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Customer Details Modal -->
    <div v-if="showViewModal" class="admin-modal">
      <div class="admin-modal__content">
        <div class="admin-modal__header">
          <h3 class="admin-modal__title">Customer Information</h3>
          <button @click="closeModal" class="admin-modal__close">&times;</button>
        </div>
        <div class="admin-modal__body">
          <div class="info-grid">
            <div class="info-item">
              <label>Name</label>
              <span>{{ selectedCustomer.name }}</span>
            </div>
            <div class="info-item">
              <label>Email</label>
              <span>{{ selectedCustomer.email }}</span>
            </div>
            <div class="info-item">
              <label>Phone</label>
              <span>{{ selectedCustomer.phone }}</span>
            </div>
            <div class="info-item">
              <label>Address</label>
              <span>{{ selectedCustomer.address }}</span>
            </div>
            <div class="info-item">
              <label>Account Status</label>
              <span :class="{'text-success': selectedCustomer.active, 'text-danger': !selectedCustomer.active}">
                {{ selectedCustomer.active ? 'Active' : 'Blocked' }}
              </span>
            </div>
          </div>

          <div class="service-history mt-4">
            <h6>Service History</h6>
            <div class="history-stats">
              <div class="stat-item">
                <label>Total Requests</label>
                <span>{{ selectedCustomer.service_requests?.length || 0 }}</span>
              </div>
              <div class="stat-item">
                <label>Active Requests</label>
                <span>{{ activeRequests }}</span>
              </div>
              <div class="stat-item">
                <label>Completed Services</label>
                <span>{{ completedServices }}</span>
              </div>
            </div>
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
import { useToast } from 'vue-toastification'
import '@/assets/components.css'

export default {
  setup() {
    const toast = useToast()
    return { toast }
  },
  
  data() {
    return {
      searchQuery: '',
      selectedStatus: '',
      sortKey: 'id',
      sortOrder: 'asc',
      showViewModal: false,
      selectedCustomer: null
    }
  },

  computed: {
    ...mapState('admin', ['customers', 'loading', 'error']),
    
    activeRequests() {
      if (!this.selectedCustomer?.service_requests) return 0
      return this.selectedCustomer.service_requests.filter(req => 
        ['pending', 'assigned'].includes(req.status?.toLowerCase())
      ).length
    },

    completedServices() {
      if (!this.selectedCustomer?.service_requests) return 0
      return this.selectedCustomer.service_requests.filter(req => 
        req.status?.toLowerCase() === 'completed'
      ).length
    },

    filteredCustomers() {
      if (!this.customers) return []
      
      return this.customers.filter(customer => {
        if (!customer) return false
        
        const searchLower = this.searchQuery.toLowerCase()
        const name = customer.name || ''
        const email = customer.email || ''
        const phone = customer.phone || ''
        
        return (
          name.toLowerCase().includes(searchLower) ||
          email.toLowerCase().includes(searchLower) ||
          phone.toLowerCase().includes(searchLower)
        ) && (
          this.selectedStatus === '' || customer.status === this.selectedStatus
        )
      }).sort((a, b) => {
        let aVal = a[this.sortKey]
        let bVal = b[this.sortKey]
        
        if (typeof aVal === 'string') {
          aVal = aVal.toLowerCase()
          bVal = bVal.toLowerCase()
        }
        
        if (aVal === bVal) return 0
        const modifier = this.sortOrder === 'asc' ? 1 : -1
        return aVal < bVal ? -1 * modifier : modifier
      })
    }
  },

  methods: {
    ...mapActions('admin', ['fetchCustomers']),

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
    },

    async blockCustomer(customer) {
      try {
        const response = await this.$store.dispatch('admin/updateUserStatus', {
          userId: customer.id,
          active: false
        })
        this.toast.success('Customer blocked successfully')
        await this.fetchCustomers()
      } catch (error) {
        console.error('Block customer error:', error)
        const message = error?.response?.data?.message || error?.message || 'Error blocking customer'
        this.toast.error(message)
      }
    },

    async unblockCustomer(customer) {
      try {
        const response = await this.$store.dispatch('admin/updateUserStatus', {
          userId: customer.id,
          active: true
        })
        this.toast.success('Customer unblocked successfully')
        await this.fetchCustomers()
      } catch (error) {
        console.error('Unblock customer error:', error)
        const message = error?.response?.data?.message || error?.message || 'Error unblocking customer'
        this.toast.error(message)
      }
    },

    viewDetails(customer) {
      this.selectedCustomer = customer
      this.showViewModal = true
    },

    closeModal() {
      this.showViewModal = false
      this.selectedCustomer = null
    }
  },

  created() {
    this.fetchCustomers()
  }
}
</script>

<style scoped>
.customer-stats {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.customer-stats h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.customer-stats-item {
  margin-bottom: 0.5rem;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  display: inline-block;
}

.status-active {
  background-color: var(--success-color);
  color: white;
}

.status-inactive {
  background-color: var(--danger-color);
  color: white;
}

.action-buttons {
  display: flex;
  gap: 6px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-item label {
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #666;
}

.text-success {
  color: #28a745;
}

.text-danger {
  color: #dc3545;
}

.service-history {
  border-top: 1px solid #dee2e6;
  padding-top: 1rem;
}

.history-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-top: 1rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
}

.stat-item label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #666;
}
</style>
