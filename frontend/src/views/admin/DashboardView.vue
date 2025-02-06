<template>
  <div class="container-fluid py-4">
    <h1 class="mb-4">Admin Dashboard</h1>
    
    <!-- Stats Overview -->
    <div class="row g-4 mb-4">
      <!-- Total Services -->
      <div class="col-md-3">
        <div class="card bg-primary text-white h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h6 class="card-title mb-0">Total Services</h6>
                <h2 class="mt-2 mb-0">{{ stats.services?.total_requests || 0 }}</h2>
              </div>
              <i class="bi bi-tools fs-1"></i>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Active Professionals -->
      <div class="col-md-3">
        <div class="card bg-success text-white h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h6 class="card-title mb-0">Active Professionals</h6>
                <h2 class="mt-2 mb-0">{{ stats.professionals?.total || 0 }}</h2>
              </div>
              <i class="bi bi-person-badge fs-1"></i>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Total Customers -->
      <div class="col-md-3">
        <div class="card bg-info text-white h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h6 class="card-title mb-0">Total Customers</h6>
                <h2 class="mt-2 mb-0">{{ stats.customers?.total || 0 }}</h2>
              </div>
              <i class="bi bi-people fs-1"></i>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Pending Requests -->
      <div class="col-md-3">
        <div class="card bg-warning text-white h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h6 class="card-title mb-0">Pending Requests</h6>
                <h2 class="mt-2 mb-0">{{ (stats.services?.status_breakdown?.requested) || 0 }}</h2>
              </div>
              <i class="bi bi-clock-history fs-1"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="row g-4 mb-4">
      <!-- Service Distribution -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">Service Status Distribution</h5>
            <canvas ref="serviceDistributionChart"></canvas>
          </div>
        </div>
      </div>
      
      <!-- Professional Status -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">Professional Performance</h5>
            <canvas ref="professionalStatusChart"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Activity and Alerts -->
    <div class="row g-4">
      <!-- Recent Service Requests -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title d-flex justify-content-between align-items-center">
              Recent Service Requests
              <button class="btn btn-sm btn-outline-primary" @click="refreshStats">
                <i class="bi bi-arrow-clockwise"></i>
              </button>
            </h5>
            <div class="table-responsive">
              <table class="table table-hover">
                <thead>
                  <tr>
                    <th>Service</th>
                    <th>Customer</th>
                    <th>Date</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!stats.services?.recent_requests?.length">
                    <td colspan="4" class="text-center">No recent requests</td>
                  </tr>
                  <tr v-for="request in stats.services?.recent_requests" :key="request.id">
                    <td>{{ request.service_name }}</td>
                    <td>{{ request.customer_name }}</td>
                    <td>{{ formatDate(request.date) }}</td>
                    <td>
                      <span :class="getStatusBadgeClass(request.status)">
                        {{ request.status }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Pending Professionals -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">Pending Professional Approvals</h5>
            <div class="table-responsive">
              <table class="table table-hover">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Service Type</th>
                    <th>Experience</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!stats.professionals?.pending?.length">
                    <td colspan="4" class="text-center">No pending approvals</td>
                  </tr>
                  <tr v-for="pro in stats.professionals?.pending" :key="pro.id">
                    <td>{{ pro.name }}</td>
                    <td>{{ pro.service_type }}</td>
                    <td>{{ pro.experience }}</td>
                    <td>
                      <button class="btn btn-sm btn-success me-1" @click="approveProfessional(pro.id)">
                        <i class="bi bi-check-lg"></i>
                      </button>
                      <button class="btn btn-sm btn-danger" @click="rejectProfessional(pro.id)">
                        <i class="bi bi-x-lg"></i>
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
import { ref, onMounted, nextTick } from 'vue'
import Chart from 'chart.js/auto'
import { useStore } from 'vuex'
import axios from 'axios'

export default {
  name: 'AdminDashboard',
  
  setup() {
    const store = useStore()
    const stats = ref({})
    const serviceDistributionChart = ref(null)
    const professionalStatusChart = ref(null)
    let charts = []
    
    // Initialize charts
    const initCharts = () => {
      console.log('Initializing charts...')
      console.log('Service chart ref:', serviceDistributionChart.value)
      console.log('Professional chart ref:', professionalStatusChart.value)
      
      // Clear existing charts
      charts.forEach(chart => chart.destroy())
      charts = []

      // Service Distribution Chart
      if (stats.value.services?.status_breakdown && serviceDistributionChart.value) {
        console.log('Creating service distribution chart with data:', stats.value.services.status_breakdown)
        const serviceChart = new Chart(serviceDistributionChart.value, {
          type: 'doughnut',
          data: {
            labels: Object.keys(stats.value.services.status_breakdown),
            datasets: [{
              data: Object.values(stats.value.services.status_breakdown),
              backgroundColor: [
                '#4CAF50', // completed
                '#FFC107', // requested
                '#2196F3', // accepted
                '#FF5722', // cancelled
                '#9C27B0'  // other
              ]
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: {
                position: 'right'
              }
            }
          }
        })
        charts.push(serviceChart)
      }

      // Professional Performance Chart
      if (stats.value.professionals && professionalStatusChart.value) {
        console.log('Creating professional performance chart')
        const proData = {
          labels: ['Total Requests', 'Completed', 'Accepted', 'Rejected'],
          data: [
            stats.value.professionals.total_requests || 0,
            stats.value.professionals.completed_requests || 0,
            stats.value.professionals.accepted_requests || 0,
            stats.value.professionals.rejected_requests || 0
          ]
        }
        
        const proChart = new Chart(professionalStatusChart.value, {
          type: 'bar',
          data: {
            labels: proData.labels,
            datasets: [{
              label: 'Request Counts',
              data: proData.data,
              backgroundColor: '#2196F3'
            }]
          },
          options: {
            responsive: true,
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  stepSize: 1
                }
              }
            }
          }
        })
        charts.push(proChart)
      }
    }

    // Fetch dashboard stats
    const fetchStats = async () => {
      try {
        console.log('Fetching stats...')
        const response = await axios.get('/api/stats/admin')
        console.log('Stats response:', response.data)
        stats.value = response.data
        await nextTick() // Wait for DOM update
        initCharts()
      } catch (error) {
        console.error('Error fetching stats:', error)
      }
    }

    const refreshStats = () => {
      fetchStats()
    }

    const formatDate = (date) => {
      return new Date(date).toLocaleDateString()
    }

    const getStatusBadgeClass = (status) => {
      const classes = {
        pending: 'badge bg-warning',
        approved: 'badge bg-success',
        rejected: 'badge bg-danger',
        completed: 'badge bg-info'
      }
      return classes[status] || 'badge bg-secondary'
    }

    onMounted(() => {
      fetchStats()
    })

    return {
      stats,
      serviceDistributionChart,
      professionalStatusChart,
      refreshStats,
      formatDate,
      getStatusBadgeClass
    }
  }
}
</script>

<style scoped>
.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-2px);
}

.table {
  margin-bottom: 0;
}

.bi {
  opacity: 0.8;
}

.badge {
  font-weight: 500;
}
</style>
