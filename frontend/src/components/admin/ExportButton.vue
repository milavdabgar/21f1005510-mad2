<template>
  <div>
    <button 
      class="btn btn-secondary"
      :class="{ 'disabled': !isApproved || loading }"
      @click="exportRequests"
      :disabled="!isApproved || loading"
    >
      <i class="fas fa-file-export me-1"></i>
      {{ loading ? 'Exporting...' : 'Export' }}
    </button>

    <div 
      v-if="snackbar.show" 
      class="alert"
      :class="snackbar.color === 'success' ? 'alert-success' : 'alert-danger'"
      role="alert"
    >
      {{ snackbar.text }}
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'ExportButton',
  props: {
    professionalId: {
      type: Number,
      required: true
    },
    isApproved: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      loading: false,
      snackbar: {
        show: false,
        text: '',
        color: 'success'
      }
    }
  },
  methods: {
    async exportRequests() {
      this.loading = true
      try {
        await api.post(`/admin/export/service-requests/${this.professionalId}`)
        this.snackbar = {
          show: true,
          text: 'Export started. You will receive the file via email.',
          color: 'success'
        }
        // Hide success message after 3 seconds
        setTimeout(() => {
          this.snackbar.show = false
        }, 3000)
      } catch (error) {
        this.snackbar = {
          show: true,
          text: 'Failed to start export',
          color: 'danger'
        }
        // Hide error message after 5 seconds
        setTimeout(() => {
          this.snackbar.show = false
        }, 5000)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.alert {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  min-width: 200px;
  max-width: 400px;
  padding: 1rem;
  margin: 0;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn.disabled {
  cursor: not-allowed;
  opacity: 0.65;
}
</style>
