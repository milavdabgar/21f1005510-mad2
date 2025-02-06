<template>
  <div class="dashboard-view">
    <div class="container py-4">
      <h1 class="mb-4">Dashboard</h1>
      
      <div class="row">
        <div class="col-md-4">
          <div class="card mb-4">
            <div class="card-body">
              <h5 class="card-title">Profile</h5>
              <p class="card-text" v-if="currentUser">
                <strong>Name:</strong> {{ currentUser.name }}<br>
                <strong>Email:</strong> {{ currentUser.email }}<br>
                <strong>Phone:</strong> {{ currentUser.phone }}<br>
                <strong>Type:</strong> {{ currentUser.type }}
              </p>
            </div>
          </div>
        </div>

        <!-- Professional specific content -->
        <template v-if="isProfessional">
          <div class="col-md-8">
            <div class="card mb-4">
              <div class="card-body">
                <h5 class="card-title">Professional Status</h5>
                <p class="card-text">
                  <strong>Service Type:</strong> {{ currentUser.service_type }}<br>
                  <strong>Experience:</strong> {{ currentUser.experience }} years<br>
                  <strong>Status:</strong> 
                  <span :class="getStatusClass">{{ currentUser.status }}</span>
                </p>
              </div>
            </div>
          </div>
        </template>

        <!-- Customer specific content -->
        <template v-if="isCustomer">
          <div class="col-md-8">
            <div class="card mb-4">
              <div class="card-body">
                <h5 class="card-title">Service History</h5>
                <p class="card-text text-muted" v-if="!hasServiceHistory">
                  No service history yet.
                </p>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'DashboardView',
  setup() {
    const store = useStore()

    const currentUser = computed(() => store.getters['auth/currentUser'])
    const isProfessional = computed(() => store.getters['auth/isProfessional'])
    const isCustomer = computed(() => store.getters['auth/isCustomer'])
    const hasServiceHistory = computed(() => false) // TODO: Implement service history

    const getStatusClass = computed(() => {
      const status = currentUser.value?.status
      return {
        'badge bg-warning': status === 'pending',
        'badge bg-success': status === 'approved',
        'badge bg-danger': status === 'rejected'
      }
    })

    return {
      currentUser,
      isProfessional,
      isCustomer,
      hasServiceHistory,
      getStatusClass
    }
  }
}
</script>

<style scoped>
.dashboard-view {
  min-height: calc(100vh - var(--navbar-height));
  background-color: var(--body-bg);
}

.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}
</style>
