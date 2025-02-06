<template>
  <div class="summary-view">
    <div class="container">
      <div v-if="error" class="alert alert-danger" role="alert">
        {{ error }}
      </div>

      <h2 class="text-center mb-4">Service Summary</h2>

      <!-- Overview Cards -->
      <div class="row mb-4">
        <div class="col-md-3">
          <div class="card bg-primary text-white">
            <div class="card-body">
              <h5 class="card-title">Total Spent</h5>
              <h3 class="mb-0">₹{{ totalSpent }}</h3>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-success text-white">
            <div class="card-body">
              <h5 class="card-title">Services Used</h5>
              <h3 class="mb-0">{{ totalServices }}</h3>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-info text-white">
            <div class="card-body">
              <h5 class="card-title">Avg Service Rating</h5>
              <h3 class="mb-0">{{ averageRating }}/5</h3>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-warning text-white">
            <div class="card-body">
              <h5 class="card-title">Active Services</h5>
              <h3 class="mb-0">{{ activeServices }}</h3>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <!-- Monthly Spending Chart -->
        <div class="col-md-8">
          <div class="card mb-4">
            <div class="card-header">
              <h3>Monthly Service Usage</h3>
            </div>
            <div class="card-body">
              <canvas ref="monthlyChart"></canvas>
            </div>
          </div>
        </div>

        <!-- Service Category Distribution -->
        <div class="col-md-4">
          <div class="card mb-4">
            <div class="card-header">
              <h3>Service Categories</h3>
            </div>
            <div class="card-body">
              <canvas ref="categoryChart"></canvas>
            </div>
          </div>
        </div>

        <!-- Service Status Distribution -->
        <div class="col-md-12">
          <div class="card">
            <div class="card-header">
              <h3>Service History</h3>
            </div>
            <div class="card-body">
              <div class="status-bars">
                <div v-for="status in statusDistribution" :key="status.name" class="status-bar">
                  <span class="status-name">{{ status.name }}</span>
                  <div class="progress">
                    <div 
                      class="progress-bar" 
                      :class="status.color"
                      :style="{ width: status.percentage + '%' }"
                    >
                      {{ status.count }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import customerService from '@/services/customer'
import Chart from 'chart.js/auto'

export default {
  name: 'CustomerSummaryView',
  setup() {
    const error = ref('')
    const statusDistribution = ref([])
    const monthlyChart = ref(null)
    const categoryChart = ref(null)
    const totalSpent = ref(0)
    const totalServices = ref(0)
    const averageRating = ref(0)
    const activeServices = ref(0)

    let charts = {
      monthly: null,
      category: null
    }

    const showError = (message) => {
      error.value = message
      setTimeout(() => error.value = '', 3000)
    }

    const calculateTotalSpent = (requests) => {
      return requests
        .filter(req => req.status === 'completed')
        .reduce((total, req) => total + (req.amount || 0), 0)
    }

    const calculateAverageRating = (requests) => {
      const ratedRequests = requests.filter(req => req.rating)
      if (ratedRequests.length === 0) return 0
      const totalRating = ratedRequests.reduce((sum, req) => sum + req.rating, 0)
      return (totalRating / ratedRequests.length).toFixed(1)
    }

    const getMonthlyData = (requests) => {
      const last6Months = Array.from({ length: 6 }, (_, i) => {
        const d = new Date()
        d.setMonth(d.getMonth() - i)
        return d.toISOString().slice(0, 7) // YYYY-MM format
      }).reverse()

      const monthlyServices = last6Months.map(month => 
        requests.filter(req => 
          req.status === 'completed' && 
          req.completedAt?.startsWith(month)
        ).length
      )

      const monthlySpending = last6Months.map(month =>
        requests
          .filter(req => 
            req.status === 'completed' && 
            req.completedAt?.startsWith(month)
          )
          .reduce((sum, req) => sum + (req.amount || 0), 0) / 1000 // Convert to thousands
      )

      return {
        services: monthlyServices,
        spending: monthlySpending,
        labels: last6Months.map(month => {
          const [year, monthNum] = month.split('-')
          const date = new Date(year, monthNum - 1)
          return date.toLocaleString('default', { month: 'short' })
        })
      }
    }

    const getCategoryData = (requests) => {
      return requests.reduce((acc, req) => {
        const category = req.service?.category || 'Other'
        acc[category] = (acc[category] || 0) + 1
        return acc
      }, {})
    }

    const initializeCharts = () => {
      // Monthly usage chart
      const monthlyCtx = monthlyChart.value.getContext('2d')
      charts.monthly = new Chart(monthlyCtx, {
        type: 'line',
        data: {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
          datasets: [{
            label: 'Services Used',
            data: [0, 0, 0, 0, 0, 0],
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
          }, {
            label: 'Amount Spent (₹1000)',
            data: [0, 0, 0, 0, 0, 0],
            borderColor: 'rgb(255, 159, 64)',
            tension: 0.1
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: 'top',
            },
            title: {
              display: true,
              text: 'Monthly Service Usage'
            }
          }
        }
      })

      // Service category distribution chart
      const categoryCtx = categoryChart.value.getContext('2d')
      charts.category = new Chart(categoryCtx, {
        type: 'doughnut',
        data: {
          labels: ['Plumbing', 'Electrical', 'Carpentry', 'Other'],
          datasets: [{
            data: [0, 0, 0, 0],
            backgroundColor: [
              'rgb(255, 99, 132)',
              'rgb(54, 162, 235)',
              'rgb(255, 205, 86)',
              'rgb(75, 192, 192)'
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
    }

    const updateCharts = (requests) => {
      if (!charts.monthly || !charts.category) return

      // Update monthly chart with real data
      const monthlyData = getMonthlyData(requests)
      charts.monthly.data.labels = monthlyData.labels
      charts.monthly.data.datasets[0].data = monthlyData.services
      charts.monthly.data.datasets[1].data = monthlyData.spending
      charts.monthly.update()

      // Update category chart with real data
      const categoryData = getCategoryData(requests)
      charts.category.data.labels = Object.keys(categoryData)
      charts.category.data.datasets[0].data = Object.values(categoryData)
      charts.category.update()
    }

    const loadSummary = async () => {
      try {
        const requestsResponse = await customerService.getRequests()
        const requests = requestsResponse.items || []
        
        // Calculate metrics
        totalSpent.value = calculateTotalSpent(requests)
        totalServices.value = requests.filter(req => req.status === 'completed').length
        averageRating.value = calculateAverageRating(requests)
        activeServices.value = requests.filter(req => 
          ['pending', 'accepted', 'in_progress'].includes(req.status)
        ).length

        // Calculate status distribution
        const statusCounts = requests.reduce((acc, req) => {
          acc[req.status] = (acc[req.status] || 0) + 1
          return acc
        }, {})

        const statusColors = {
          completed: 'bg-success',
          in_progress: 'bg-info',
          pending: 'bg-warning',
          cancelled: 'bg-danger',
          rejected: 'bg-secondary'
        }

        const distribution = Object.entries(statusCounts).map(([status, count]) => ({
          name: status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' '),
          count,
          percentage: (count / requests.length) * 100,
          color: statusColors[status] || 'bg-primary'
        }))

        statusDistribution.value = distribution
        
        // Update charts with real data
        updateCharts(requests)
      } catch (err) {
        showError('Failed to load summary data')
        console.error(err)
      }
    }

    onMounted(() => {
      loadSummary()
      initializeCharts()
    })

    onUnmounted(() => {
      // Cleanup charts
      Object.values(charts).forEach(chart => {
        if (chart) chart.destroy()
      })
    })

    return {
      error,
      statusDistribution,
      monthlyChart,
      categoryChart,
      totalSpent,
      totalServices,
      averageRating,
      activeServices
    }
  }
}
</script>

<style scoped>
.summary-view {
  padding: 2rem 0;
}

.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  border: none;
  margin-bottom: 1rem;
}

.card-header {
  background-color: #fff;
  border-bottom: 1px solid rgba(0, 0, 0, 0.125);
}

.bg-primary {
  background-color: #4e73df !important;
}

.bg-success {
  background-color: #1cc88a !important;
}

.bg-info {
  background-color: #36b9cc !important;
}

.bg-warning {
  background-color: #f6c23e !important;
}

.card-title {
  margin-bottom: 0.5rem;
  font-size: 0.8rem;
  text-transform: uppercase;
}

canvas {
  max-height: 300px;
}

.status-bars {
  margin-top: 1rem;
}

.status-bar {
  margin-bottom: 1rem;
}

.status-name {
  display: inline-block;
  width: 120px;
  text-transform: capitalize;
}

.progress {
  height: 1.5rem;
  margin-top: 0.25rem;
}
</style>
