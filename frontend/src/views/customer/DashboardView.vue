// src/views/customer/DashboardView.vue
<template>
  <div class="container py-4">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Welcome {{ user?.name }}</h2>
      <button 
        @click="refreshData" 
        class="btn btn-outline-primary"
      >
        Refresh
      </button>
    </div>

    <!-- Stats Overview -->
    <div class="row mb-4">
      <div class="col-md-3">
        <div class="card shadow-sm p-3">
          <div class="d-flex justify-content-between">
            <div>
              <h3 class="mb-0">{{ stats.total_requests || 0 }}</h3>
              <span class="text-muted">Total Requests</span>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card shadow-sm p-3">
          <div class="d-flex justify-content-between">
            <div>
              <h3 class="mb-0">{{ stats.pending_requests || 0 }}</h3>
              <span class="text-muted">Active Requests</span>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card shadow-sm p-3">
          <div class="d-flex justify-content-between">
            <div>
              <h3 class="mb-0">{{ stats.completed_requests || 0 }}</h3>
              <span class="text-muted">Completed Services</span>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card shadow-sm p-3">
          <div class="d-flex justify-content-between">
            <div>
              <h3 class="mb-0">₹{{ stats.total_spending || 0 }}</h3>
              <span class="text-muted">Total Spending</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Service Categories -->
    <h3 class="mb-3">Looking For?</h3>
    <div class="row g-4">
      <div class="col-md-6" v-for="category in categories" :key="category.name">
        <div class="card shadow-sm h-100" style="cursor: pointer" @click="goToServices(category.name)">
          <div class="card-body">
            <h5 class="card-title">{{ category.name }}</h5>
            <p class="card-text">{{ category.description }}</p>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card shadow-sm h-100 bg-primary text-white" style="cursor: pointer" @click="goToServices()">
          <div class="card-body d-flex flex-column align-items-center justify-content-center text-center">
            <i class="fas fa-list-ul fa-2x mb-2"></i>
            <h5 class="card-title mb-2">View All Services</h5>
            <p class="card-text">Browse our complete catalog of services</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'DashboardView',

  setup() {
    const store = useStore()
    const router = useRouter()
    
    const stats = ref({})
    const user = computed(() => store.state.auth.user)
    const categories = ref([
      {
        name: 'Cleaning',
        description: 'Professional cleaning services for your needs'
      },
      {
        name: 'Repair',
        description: 'Professional repair services for your needs'
      },
      {
        name: 'Plumbing',
        description: 'Professional plumbing services for your needs'
      },
      {
        name: 'Electrical',
        description: 'Professional electrical services for your needs'
      },
      {
        name: 'Painting',
        description: 'Professional painting services for your needs'
      }
    ])

    const loadDashboardData = async () => {
      try {
        await store.dispatch('customer/fetchDashboardStats')
        
        stats.value = store.state.customer.dashboardStats
      } catch (error) {
        console.error('Error loading dashboard data:', error)
      }
    }

    onMounted(async () => {
      await loadDashboardData()
    })

    const refreshData = () => {
      loadDashboardData()
    }

    const goToServices = (type) => {
      router.push({
        name: 'customer.services',
        query: { type }
      })
    }

    return {
      user,
      stats,
      categories,
      goToServices,
      refreshData
    }
  }
}
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.cursor-pointer:hover {
  transform: translateY(-2px);
  transition: transform 0.2s ease;
}
</style>