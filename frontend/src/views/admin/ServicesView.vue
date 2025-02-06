<template>
  <div class="container mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold mb-6">Services</h1>

    <!-- Search and Filter -->
    <div class="filters">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="Search services..." 
        class="form-control"
      >
      <select v-model="selectedType" class="form-control">
        <option value="">All Types</option>
        <option v-for="category in serviceCategories" 
                :key="category.type" 
                :value="category.type">
          {{ category.name }}
        </option>
      </select>
      <button @click="showNewServiceModal = true" class="btn btn-success">
        <i class="fas fa-plus"></i>
        New
      </button>
    </div>

    <!-- Services Table -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th @click="toggleSort('id')" :class="{'asc': sortBy === 'id' && sortDesc, 'desc': sortBy === 'id' && !sortDesc}">ID</th>
            <th @click="toggleSort('name')" :class="{'asc': sortBy === 'name' && sortDesc, 'desc': sortBy === 'name' && !sortDesc}">Name</th>
            <th @click="toggleSort('type')" :class="{'asc': sortBy === 'type' && sortDesc, 'desc': sortBy === 'type' && !sortDesc}">Type</th>
            <th @click="toggleSort('price')" :class="{'asc': sortBy === 'price' && sortDesc, 'desc': sortBy === 'price' && !sortDesc}">Price</th>
            <th @click="toggleSort('time_required')" :class="{'asc': sortBy === 'time_required' && sortDesc, 'desc': sortBy === 'time_required' && !sortDesc}">Time Required</th>
            <th @click="toggleSort('status')" :class="{'asc': sortBy === 'status' && sortDesc, 'desc': sortBy === 'status' && !sortDesc}">Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="service in filteredServices" :key="service.id">
            <td class="clickable" @click="viewService(service)">{{ service.id }}</td>
            <td class="clickable" @click="viewService(service)">{{ service.name }}</td>
            <td>{{ service.type }}</td>
            <td>₹{{ service.price }}</td>
            <td>{{ service.time_required }}</td>
            <td>
              <span class="status-badge" :class="'status-' + (service.status || 'active').toLowerCase()">
                {{ service.status || 'Active' }}
              </span>
            </td>
            <td>
              <div class="action-buttons">
                <button @click="editService(service)" class="btn btn-sm btn-primary">Edit</button>
                <button @click="deleteService(service.id)" class="btn btn-sm btn-danger">Delete</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- View Service Modal -->
    <div v-if="showViewModal" class="admin-modal">
      <div class="admin-modal__content">
        <div class="admin-modal__header">
          <h3 class="admin-modal__title">Service Information</h3>
          <button @click="showViewModal = false" class="admin-modal__close">&times;</button>
        </div>
        <div class="admin-modal__body">
          <div class="details-list">
            <div class="details-item">
              <div class="details-label">Name</div>
              <div class="details-value">{{ selectedService.name }}</div>
            </div>
            <div class="details-item">
              <div class="details-label">Type</div>
              <div class="details-value">{{ selectedService.type }}</div>
            </div>
            <div class="details-item">
              <div class="details-label">Price</div>
              <div class="details-value">₹{{ selectedService.price }}</div>
            </div>
            <div class="details-item">
              <div class="details-label">Status</div>
              <div class="details-value">
                <span class="status-badge" :class="'status-' + (selectedService?.status || 'active').toLowerCase()">
                  {{ selectedService?.status || 'Active' }}
                </span>
              </div>
            </div>
          </div>

          <div class="service-stats mt-4">
            <h4>Service Statistics</h4>
            <div class="service-stats-item">
              Total Requests: {{ selectedService.total_requests || 0 }}
            </div>
            <div class="service-stats-item">
              Active Professionals: {{ selectedService.active_professionals || 0 }}
            </div>
            <div class="service-stats-item">
              Average Rating: {{ selectedService.avg_rating || 'No ratings yet' }}
            </div>
          </div>

          <div class="mt-4">
            <div class="details-label">Description</div>
            <div class="service-description">{{ selectedService.description }}</div>
          </div>
        </div>
        <div class="admin-modal__footer">
          <button @click="showViewModal = false" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>

    <!-- Edit/New Service Modal -->
    <div v-if="showNewServiceModal" class="admin-modal">
      <div class="admin-modal__content">
        <div class="admin-modal__header">
          <h3 class="admin-modal__title">{{ editingService ? 'Edit' : 'New' }} Service</h3>
          <button @click="showNewServiceModal = false" class="admin-modal__close">&times;</button>
        </div>
        <div class="admin-modal__body">
          <form @submit.prevent="saveService">
            <div class="form-group">
              <label class="form-label">Name</label>
              <input v-model="serviceForm.name" type="text" class="form-control" required>
            </div>
            <div class="form-group">
              <label class="form-label">Type</label>
              <select v-model="serviceForm.type" class="form-control" required>
                <option v-for="category in serviceCategories" 
                        :key="category.type" 
                        :value="category.type">
                  {{ category.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Price (₹)</label>
              <input v-model.number="serviceForm.price" type="number" class="form-control" required min="0">
            </div>
            <div class="form-group">
              <label class="form-label">Time Required (mins)</label>
              <input v-model="serviceForm.time_required" type="text" class="form-control" required>
            </div>
            <div class="form-group">
              <label class="form-label">Description</label>
              <textarea v-model="serviceForm.description" class="form-control" rows="3"></textarea>
            </div>
          </form>
        </div>
        <div class="admin-modal__footer">
          <button type="button" @click="showNewServiceModal = false" class="btn btn-secondary">Cancel</button>
          <button type="submit" @click="saveService" class="btn btn-primary">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'

export default {
  name: 'ServicesView',
  
  data() {
    return {
      searchQuery: '',
      selectedType: '',
      showNewServiceModal: false,
      showViewModal: false,
      selectedService: null,
      serviceForm: {
        name: '',
        type: '',
        price: 0,
        time_required: '',
        description: ''
      },
      editingService: null,
      sortBy: 'id',
      sortDesc: true,
    }
  },

  computed: {
    ...mapState('admin', ['services', 'serviceCategories', 'loading', 'error']),
    
    filteredServices() {
      let result = [...this.services]

      // Apply search filter
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        result = result.filter(service => 
          service.name.toLowerCase().includes(query) ||
          service.type.toLowerCase().includes(query)
        )
      }

      // Apply type filter
      if (this.selectedType) {
        result = result.filter(service => 
          service.type === this.selectedType
        )
      }

      // Apply sorting
      result.sort((a, b) => {
        let aVal = a[this.sortBy]
        let bVal = b[this.sortBy]
        
        // Handle numeric values
        if (this.sortBy === 'price') {
          aVal = Number(aVal)
          bVal = Number(bVal)
        }
        
        if (aVal < bVal) return this.sortDesc ? 1 : -1
        if (aVal > bVal) return this.sortDesc ? -1 : 1
        return 0
      })

      return result
    }
  },

  methods: {
    ...mapActions('admin', ['fetchServices', 'fetchServiceCategories', 'createService', 'updateService', 'deleteService']),

    async refreshServices() {
      try {
        await this.fetchServices()
      } catch (error) {
        console.error('Error refreshing services:', error)
      }
    },

    getStatusClass(status) {
      return {
        'active': 'px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800',
        'inactive': 'px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800'
      }[status] || ''
    },

    toggleSort(field) {
      if (this.sortBy === field) {
        this.sortDesc = !this.sortDesc
      } else {
        this.sortBy = field
        this.sortDesc = true
      }
    },

    getSortIcon(field) {
      if (this.sortBy !== field) return '↕'
      return this.sortDesc ? '↓' : '↑'
    },

    async saveService() {
      try {
        const formData = {
          name: this.serviceForm.name.trim(),
          type: this.serviceForm.type,
          price: Number(this.serviceForm.price),
          time_required: this.serviceForm.time_required.trim(),
          description: (this.serviceForm.description || '').trim()
        }
        
        if (this.editingService) {
          await this.updateService({
            id: this.editingService.id,
            ...formData
          })
          alert('Service updated successfully')
        } else {
          await this.createService(formData)
          alert('Service created successfully')
        }
        
        this.showNewServiceModal = false
        this.resetForm()
      } catch (error) {
        console.error('Error saving service:', error)
        const errorMessage = error.response?.data?.message || error.message || 'Failed to save service'
        alert(errorMessage)
      }
    },

    async deleteService(id) {
      if (confirm('Are you sure you want to delete this service?')) {
        try {
          await this.$store.dispatch('admin/deleteService', id)
          alert('Service deleted successfully')
        } catch (error) {
          console.error('Error deleting service:', error)
          const errorMessage = error.response?.data?.message || error.message || 'Failed to delete service'
          alert(errorMessage)
        }
      }
    },

    editService(service) {
      this.editingService = service
      this.serviceForm = {
        name: service.name,
        type: service.type,
        price: Number(service.price),
        time_required: service.time_required,
        description: service.description || ''
      }
      this.showNewServiceModal = true
    },

    resetForm() {
      this.serviceForm = {
        name: '',
        type: '',
        price: 0,
        time_required: '',
        description: ''
      }
      this.editingService = null
    },

    viewService(service) {
      this.selectedService = service ? { ...service } : null
      this.showViewModal = true
    },
  },

  created() {
    this.fetchServices()
    this.fetchServiceCategories()
  },

  watch: {
    // Watch route changes to refresh data
    '$route'() {
      this.fetchServices()
    }
  }
}
</script>

<style scoped>
.service-stats {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.service-stats h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.service-stats-item {
  margin-bottom: 0.5rem;
}

.service-description {
  margin-top: 0.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
  white-space: pre-wrap;
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

.filters {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.clickable {
  cursor: pointer;
}
</style>
