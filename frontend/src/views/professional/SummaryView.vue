<template>
  <div class="summary-view">
    <div class="container">
      <div v-if="error" class="alert alert-danger" role="alert">
        {{ error }}
      </div>

      <h2 class="text-center mb-4">Performance Summary</h2>

      <!-- Performance Overview Cards -->
      <div class="row mb-4">
        <div class="col-md-3">
          <div class="card bg-primary text-white">
            <div class="card-body">
              <h5 class="card-title">Total Earnings</h5>
              <h3 class="mb-0">₹{{ totalEarnings }}</h3>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-success text-white">
            <div class="card-body">
              <h5 class="card-title">Completion Rate</h5>
              <h3 class="mb-0">{{ completionRate }}%</h3>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-info text-white">
            <div class="card-body">
              <h5 class="card-title">Avg Rating</h5>
              <h3 class="mb-0">{{ averageRating }}/5</h3>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-warning text-white">
            <div class="card-body">
              <h5 class="card-title">Response Time</h5>
              <h3 class="mb-0">{{ avgResponseTime }}h</h3>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <!-- Monthly Performance Chart -->
        <div class="col-md-8">
          <div class="card mb-4">
            <div class="card-header">
              <h3>Monthly Performance</h3>
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

        <!-- Ratings Distribution -->
        <div class="col-md-12">
          <div class="card">
            <div class="card-header">
              <h3>Your Ratings Distribution</h3>
            </div>
            <div class="card-body">
              <div class="ratings-chart">
                <div v-for="rating in ratingsDistribution" :key="rating.stars" class="rating-bar">
                  <span class="stars">{{ rating.stars }} Stars</span>
                  <div class="progress">
                    <div 
                      class="progress-bar bg-primary" 
                      :style="{ width: rating.percentage + '%' }"
                    >
                      {{ rating.count }}
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
import professionalService from '@/services/professional'
import Chart from 'chart.js/auto'

export default {
  name: 'SummaryView',
  setup() {
    const error = ref('')
    const ratingsDistribution = ref([])
    const monthlyChart = ref(null)
    const categoryChart = ref(null)
    const totalEarnings = ref(0)
    const completionRate = ref(0)
    const averageRating = ref(0)
    const avgResponseTime = ref(0)
    const stats = ref({
      completed: 0,
      closed: 0,
      rejected: 0,
      total: 0
    })

    let charts = {
      monthly: null,
      category: null
    }

    const showError = (message) => {
      error.value = message
      setTimeout(() => error.value = '', 3000)
    }

    const calculateTotalEarnings = (requests) => {
      return requests
        .filter(req => req.status === 'completed')
        .reduce((total, req) => total + (req.amount || 0), 0)
    }

    const calculateCompletionRate = (stats) => {
      if (stats.total === 0) return 0
      return Math.round((stats.completed / stats.total) * 100)
    }

    const calculateAverageRating = (requests) => {
      const ratedRequests = requests.filter(req => req.rating)
      if (ratedRequests.length === 0) return 0
      const totalRating = ratedRequests.reduce((sum, req) => sum + req.rating, 0)
      return (totalRating / ratedRequests.length).toFixed(1)
    }

    const calculateResponseTime = (requests) => {
      const respondedRequests = requests.filter(req => req.responseTime)
      if (respondedRequests.length === 0) return 0
      const totalTime = respondedRequests.reduce((sum, req) => sum + req.responseTime, 0)
      return Math.round(totalTime / respondedRequests.length)
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

      const monthlyEarnings = last6Months.map(month =>
        requests
          .filter(req => 
            req.status === 'completed' && 
            req.completedAt?.startsWith(month)
          )
          .reduce((sum, req) => sum + (req.amount || 0), 0) / 1000 // Convert to thousands
      )

      return {
        services: monthlyServices,
        earnings: monthlyEarnings
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
      // Monthly performance chart
      const monthlyCtx = monthlyChart.value.getContext('2d')
      charts.monthly = new Chart(monthlyCtx, {
        type: 'line',
        data: {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
          datasets: [{
            label: 'Completed Services',
            data: [0, 0, 0, 0, 0, 0],
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
          }, {
            label: 'Earnings (₹1000)',
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
              text: 'Monthly Performance Trends'
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
      charts.monthly.data.datasets[0].data = monthlyData.services
      charts.monthly.data.datasets[1].data = monthlyData.earnings
      charts.monthly.update()

      // Update category chart with real data
      const categoryData = getCategoryData(requests)
      charts.category.data.labels = Object.keys(categoryData)
      charts.category.data.datasets[0].data = Object.values(categoryData)
      charts.category.update()
    }

    const loadSummary = async () => {
      try {
        const requestsResponse = await professionalService.getRequests()
        const requests = requestsResponse.items || []
        
        // Calculate request statistics
        stats.value = requests.reduce((acc, req) => {
          acc.total++
          if (req.status === 'completed') acc.completed++
          if (req.status === 'closed') acc.closed++
          if (req.status === 'rejected') acc.rejected++
          return acc
        }, { completed: 0, closed: 0, rejected: 0, total: 0 })

        // Calculate other metrics
        totalEarnings.value = calculateTotalEarnings(requests)
        completionRate.value = calculateCompletionRate(stats.value)
        averageRating.value = calculateAverageRating(requests)
        avgResponseTime.value = calculateResponseTime(requests)
        
        // Update charts with real data
        updateCharts(requests)

        // Calculate ratings distribution
        const ratings = requests.filter(req => req.rating).map(req => req.rating)
        const distribution = [5, 4, 3, 2, 1].map(stars => {
          const count = ratings.filter(r => r === stars).length
          return {
            stars,
            count,
            percentage: ratings.length ? (count / ratings.length) * 100 : 0
          }
        })
        ratingsDistribution.value = distribution
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
      ratingsDistribution,
      monthlyChart,
      categoryChart,
      stats,
      totalEarnings,
      completionRate,
      averageRating,
      avgResponseTime
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

.ratings-chart {
  margin-top: 1rem;
}

.rating-bar {
  margin-bottom: 1rem;
}

.stars {
  display: inline-block;
  width: 80px;
}

.progress {
  height: 1.5rem;
  margin-top: 0.25rem;
}
</style>