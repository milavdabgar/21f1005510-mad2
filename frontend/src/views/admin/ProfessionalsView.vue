<template>
  <div class="container mx-auto px-4 py-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold mb-6">Professionals</h1>
    </div>

    <!-- Search and Filter -->
    <div class="filters">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="Search professionals..." 
        class="form-control"
      >
      <select 
        v-model="selectedStatus" 
        class="form-control"
      >
        <option value="">All Status</option>
        <option value="pending">Pending</option>
        <option value="approved">Approved</option>
        <option value="blocked">Blocked</option>
        <option value="active">Active</option>
      </select>
    </div>

    <!-- Professionals Table -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th @click="sort('id')" :class="getSortClass('id')">ID</th>
            <th @click="sort('name')" :class="getSortClass('name')">Name</th>
            <th @click="sort('service_type')" :class="getSortClass('service_type')">Service Type</th>
            <th @click="sort('experience')" :class="getSortClass('experience')">Experience</th>
            <th @click="sort('status')" :class="getSortClass('status')">Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="professional in filteredProfessionals" :key="professional.id">
            <td class="clickable" @click="viewDetails(professional)">{{ professional.id }}</td>
            <td class="clickable" @click="viewDetails(professional)">{{ professional.name }}</td>
            <td>{{ professional.service_type }}</td>
            <td>{{ professional.experience }}</td>
            <td>
              <span class="status-badge" :class="'status-' + professional.status.toLowerCase()">
                {{ professional.status }}
              </span>
            </td>
            <td>
              <div class="action-buttons">
                <button 
                  v-if="professional.status === 'pending'"
                  @click="viewDetails(professional)" 
                  class="btn btn-sm btn-primary"
                >
                  Verify
                </button>
                <button 
                  v-if="professional.active"
                  @click="blockProfessional(professional)" 
                  class="btn btn-sm btn-danger"
                >
                  Block
                </button>
                <button 
                  v-if="!professional.active"
                  @click="unblockProfessional(professional)" 
                  class="btn btn-sm btn-success"
                >
                  Unblock
                </button>
                <ExportButton 
                  :professional-id="professional.id"
                  :is-approved="professional.status === 'approved'"
                  class="btn-sm"
                />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Professional Details Modal -->
    <div v-if="selectedProfessional" class="admin-modal">
      <div class="admin-modal__content">
        <div class="admin-modal__header">
          <h3 class="admin-modal__title">Professional Information</h3>
          <button @click="closeModal" class="admin-modal__close">&times;</button>
        </div>
        <div class="admin-modal__body">
          <div class="info-grid">
            <div class="info-item">
              <label>Name</label>
              <span>{{ selectedProfessional.name }}</span>
            </div>
            <div class="info-item">
              <label>Email</label>
              <span>{{ selectedProfessional.email }}</span>
            </div>
            <div class="info-item">
              <label>Phone</label>
              <span>{{ selectedProfessional.phone }}</span>
            </div>
            <div class="info-item">
              <label>Service Type</label>
              <span>{{ selectedProfessional.service_type }}</span>
            </div>
            <div class="info-item">
              <label>Experience</label>
              <span>{{ selectedProfessional.experience }} Years</span>
            </div>
            <div class="info-item">
              <label>Account Status</label>
              <span :class="{
                'text-success': selectedProfessional.active,
                'text-danger': !selectedProfessional.active
              }">
                {{ selectedProfessional.active ? 'Active' : 'Blocked' }}
              </span>
            </div>
            <div class="info-item">
              <label>Verification Status</label>
              <span :class="{
                'text-success': selectedProfessional.status === 'approved',
                'text-warning': selectedProfessional.status === 'pending',
                'text-danger': selectedProfessional.status === 'rejected'
              }">
                {{ selectedProfessional.status }}
              </span>
            </div>
          </div>

          <!-- Documents Section -->
          <div class="details-section mt-4">
            <h4 class="section-title">Verification Documents</h4>
            <div class="documents-list">
              <div v-if="selectedProfessional.id_proof_path" class="document-link">
                <a href="#" @click.prevent="openDocument({
                  url: selectedProfessional.id_proof_path
                })">ID Proof</a>
              </div>
              <div v-if="selectedProfessional.certification_path" class="document-link">
                <a href="#" @click.prevent="openDocument({
                  url: selectedProfessional.certification_path
                })">Certification</a>
              </div>
            </div>
          </div>

          <!-- Verification Actions -->
          <div v-if="selectedProfessional.status === 'pending'" class="verification-actions mt-4">
            <div class="comment-section">
              <label for="comment">Comment (optional for verification, required for rejection):</label>
              <textarea 
                id="comment" 
                v-model="verificationComment" 
                class="form-control"
                rows="3"
              ></textarea>
            </div>
            <div class="action-buttons mt-3">
              <button 
                @click="handleVerification(true)" 
                class="btn btn-success"
                :disabled="isProcessing"
              >
                Verify Professional
              </button>
              <button 
                @click="handleVerification(false)" 
                class="btn btn-danger"
                :disabled="isProcessing || !verificationComment"
              >
                Reject Professional
              </button>
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
import ExportButton from '@/components/admin/ExportButton.vue'

export default {
  components: {
    ExportButton
  },
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
      selectedProfessional: null,
      verificationComment: '',
      isProcessing: false
    }
  },

  computed: {
    ...mapState('admin', ['professionals', 'loading', 'error', 'professionalDocuments']),
    
    apiUrl() {
      return 'http://localhost:5000'  // Your backend API URL
    },

    filteredProfessionals() {
      if (!this.professionals) return []
      
      return this.professionals.filter(professional => {
        if (!professional) return false
        
        const searchLower = this.searchQuery.toLowerCase()
        const name = professional.name || ''
        const serviceType = professional.service_type || ''
        const experience = professional.experience?.toString() || ''
        
        return (
          name.toLowerCase().includes(searchLower) ||
          serviceType.toLowerCase().includes(searchLower) ||
          experience.toLowerCase().includes(searchLower)
        ) && (
          this.selectedStatus === '' || professional.status === this.selectedStatus
        )
      }).sort((a, b) => {
        let aVal = a[this.sortKey]
        let bVal = b[this.sortKey]
        
        if (this.sortKey === 'experience') {
          aVal = parseInt(aVal) || 0
          bVal = parseInt(bVal) || 0
        } else if (typeof aVal === 'string') {
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
    ...mapActions('admin', [
      'fetchProfessionals', 
      'fetchProfessionalDocuments',
      'verifyProfessional',
      'updateUserStatus'
    ]),

    async blockProfessional(professional) {
      try {
        const response = await this.$store.dispatch('admin/updateUserStatus', {
          userId: professional.id,
          active: false
        })
        this.toast.success('Professional blocked successfully')
        await this.fetchProfessionals()
      } catch (error) {
        console.error('Block professional error:', error)
        const message = error?.response?.data?.message || error?.message || 'Error blocking professional'
        this.toast.error(message)
      }
    },

    async unblockProfessional(professional) {
      try {
        const response = await this.$store.dispatch('admin/updateUserStatus', {
          userId: professional.id,
          active: true
        })
        this.toast.success('Professional unblocked successfully')
        await this.fetchProfessionals()
      } catch (error) {
        console.error('Unblock professional error:', error)
        const message = error?.response?.data?.message || error?.message || 'Error unblocking professional'
        this.toast.error(message)
      }
    },

    async approveProfessional(professionalId) {
      try {
        const response = await this.$store.dispatch('admin/verifyProfessional', {
          professionalId,
          approved: true
        })
        this.toast.success('Professional approved successfully')
        await this.fetchProfessionals()
      } catch (error) {
        console.error('Approve professional error:', error)
        const message = error?.response?.data?.message || error?.message || 'Error approving professional'
        this.toast.error(message)
      }
    },

    openDocument(doc) {
      const token = localStorage.getItem('token')
      if (!token) {
        this.toast.error('Authentication required')
        return
      }
      
      // Extract filename from the full path
      const filename = doc.url.split('/').slice(-1)[0]
      // Get professional ID from the path
      const professionalId = doc.url.split('/')[1]
      const url = `${this.apiUrl}/api/admin/documents/${professionalId}/${filename}`
      
      // Open in new window with auth header
      const newWindow = window.open('', '_blank')
      if (newWindow) {
        newWindow.document.write('Loading document...')
        
        fetch(url, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        .then(response => response.blob())
        .then(blob => {
          const objectUrl = window.URL.createObjectURL(blob)
          newWindow.location.href = objectUrl
        })
        .catch(error => {
          newWindow.document.write('Error loading document')
          console.error('Error loading document:', error)
          this.toast.error('Error loading document')
        })
      }
    },

    async handleVerification(approved) {
      if (this.isProcessing) return
      
      this.isProcessing = true
      let errorMessage = 'Error updating professional status'
      
      try {
        await this.verifyProfessional({
          professionalId: this.selectedProfessional.id,
          approved,
          comment: this.verificationComment
        })

        await this.fetchProfessionals()
        this.closeModal()
        this.toast.success(
          approved ? 'Professional verified successfully' : 'Professional rejected successfully'
        )
      } catch (error) {
        console.error('Error verifying professional:', error)
        if (error.response?.data?.message) {
          errorMessage = error.response.data.message
        } else if (error.message) {
          errorMessage = error.message
        }
        this.toast.error(errorMessage)
      } finally {
        this.isProcessing = false
      }
    },

    async viewDetails(professional) {
      this.selectedProfessional = professional
      this.showViewModal = true
      this.verificationComment = ''
      this.isProcessing = false
      
      try {
        await this.fetchProfessionalDocuments(professional.id)
      } catch (error) {
        console.error('Error fetching documents:', error)
        this.toast.error('Error loading professional documents')
      }
    },

    closeModal() {
      this.showViewModal = false
      this.selectedProfessional = null
      this.verificationComment = ''
      this.isProcessing = false
    },

    viewDocuments() {
      // Implement document viewing logic
      console.log('View documents for:', this.selectedProfessional.id)
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
    this.fetchProfessionals()
  }
}
</script>

<style scoped>
/* Component-specific styles only */
.service-stats {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.service-stats-item {
  margin-bottom: 0.5rem;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  display: inline-block;
}

.status-pending {
  background-color: var(--warning-color);
  color: white;
}

.status-approved {
  background-color: var(--success-color);
  color: white;
}

.status-blocked {
  background-color: var(--danger-color);
  color: white;
}

.status-active {
  background-color: #007bff;
  color: white;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.documents-list {
  margin-top: 1rem;
}

.document-link {
  margin-bottom: 0.5rem;
}

.document-link a {
  color: #007bff;
  text-decoration: underline;
  cursor: pointer;
}

.document-link a:hover {
  color: #0056b3;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-item label {
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.details-section {
  margin-top: 2rem;
}

.section-title {
  font-weight: 600;
  margin-bottom: 1rem;
}

.verification-actions {
  margin-top: 2rem;
}

.comment-section {
  margin-bottom: 1rem;
}

.comment-section label {
  display: block;
  margin-bottom: 0.5rem;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  line-height: 1rem;
}

.btn-secondary {
  background-color: #6b7280;
  color: white;
}

.btn-secondary:hover {
  background-color: #4b5563;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
