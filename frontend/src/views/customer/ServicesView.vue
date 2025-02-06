<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>{{ serviceType }} Services</h2>
      <button 
        @click="$router.push('/customer/dashboard')"
        class="btn btn-outline-secondary"
      >
        Back to Dashboard
      </button>
    </div>

    <!-- Service Categories -->
    <div class="row mb-4">
      <div class="col-12">
        <div class="d-flex gap-4 justify-content-center">
          <div 
            v-for="category in categories" 
            :key="category.name"
            class="text-center category-item"
            :class="{ 'active': category.name === serviceType }"
            @click="selectCategory(category.name)"
          >
            <div class="category-icon mb-2">
              <i :class="category.icon"></i>
            </div>
            <div class="category-name">{{ category.name }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Service Filters -->
    <div class="filters-container mb-4">
      <!-- Search Bar -->
      <div class="search-bar">
        <i class="bi bi-search search-icon"></i>
        <input 
          type="text" 
          v-model="filters.search" 
          class="form-control search-input" 
          placeholder="Search for services..."
          @input="debouncedSearch"
        >
        <button 
          v-if="filters.search" 
          @click="clearSearch" 
          class="clear-search"
        >
          <i class="bi bi-x"></i>
        </button>
      </div>

      <!-- Advanced Filters -->
      <div class="advanced-filters">
        <div class="filter-group">
          <label class="filter-label">Sort By</label>
          <select 
            v-model="filters.sortBy" 
            class="form-select" 
            @change="applyFilters"
          >
            <option value="name">Name</option>
            <option value="price_low">Price: Low to High</option>
            <option value="price_high">Price: High to Low</option>
            <option value="rating">Rating</option>
          </select>
        </div>

        <div class="filter-group price-range">
          <label class="filter-label">Price Range</label>
          <div class="price-inputs">
            <div class="input-group">
              <span class="input-group-text">₹</span>
              <input 
                type="number" 
                v-model="filters.minPrice" 
                class="form-control" 
                placeholder="Min"
                @input="debouncedSearch"
              >
            </div>
            <div class="input-group">
              <span class="input-group-text">₹</span>
              <input 
                type="number" 
                v-model="filters.maxPrice" 
                class="form-control" 
                placeholder="Max"
                @input="debouncedSearch"
              >
            </div>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">Min Rating</label>
          <select 
            v-model="filters.rating" 
            class="form-select"
            @change="applyFilters"
          >
            <option value="">Any</option>
            <option value="4">4+ Stars</option>
            <option value="3">3+ Stars</option>
          </select>
        </div>

        <button 
          @click="resetFilters"
          class="btn btn-outline-secondary reset-btn"
        >
          <i class="bi bi-arrow-counterclockwise"></i>
          Reset
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-5">
      Loading services...
    </div>

    <!-- Services Grid -->
    <div v-else class="row g-4">
      <div 
        v-for="service in services" 
        :key="service.id" 
        class="col-md-6"
      >
        <div class="card h-100 service-card">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <div>
                <h4 class="mb-1">{{ service.name }}</h4>
                <div class="rating">
                  <span 
                    v-for="n in 5" 
                    :key="n" 
                    :class="{ 'text-warning': n <= service.rating }"
                  >
                    ★
                  </span>
                  <span class="text-muted ms-2">
                    {{ service.reviews_count || 'No' }} reviews
                  </span>
                </div>
              </div>
              <div class="service-price">
                <span class="price-tag">₹{{ service.base_price }}</span>
              </div>
            </div>
            
            <p class="text-muted mb-3">{{ service.description }}</p>
            
            <div class="d-flex justify-content-between align-items-center">
              <div class="service-price">
                <span class="price-tag">₹{{ service.price }}</span>
                <small class="text-muted d-block">{{ service.time_required }}</small>
              </div>
              <button 
                @click="bookService(service)"
                class="btn btn-primary"
                :disabled="bookingService === service.id"
              >
                {{ bookingService === service.id ? 'Booking...' : 'Book Now' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

export default {
  setup() {
    const route = useRoute()
    const router = useRouter()
    const loading = ref(false)
    const services = ref([])
    const serviceType = ref(route.query.type || 'All')
    const bookingService = ref(null)
    
    const categories = ref([
      { name: 'All', icon: 'bi bi-grid-fill' },
      { name: 'Cleaning', icon: 'bi bi-brush' },
      { name: 'Repair', icon: 'bi bi-tools' },
      { name: 'Plumbing', icon: 'bi bi-droplet-fill' },
      { name: 'Electrical', icon: 'bi bi-lightning-charge-fill' },
      { name: 'Painting', icon: 'bi bi-palette-fill' }
    ])

    const filters = ref({
      sortBy: 'name',
      minPrice: '',
      maxPrice: '',
      rating: '',
      search: ''
    })

    const selectCategory = (category) => {
      serviceType.value = category
      router.push({ query: { ...route.query, type: category } })
      fetchServices()
    }

    const fetchServices = async () => {
      loading.value = true
      try {
        const response = await axios.get('/api/services/', {
          params: {
            type: serviceType.value !== 'All' ? serviceType.value.toLowerCase() : undefined,
            search: filters.value.search || undefined,
            sortBy: filters.value.sortBy,
            minPrice: filters.value.minPrice || undefined,
            maxPrice: filters.value.maxPrice || undefined,
            rating: filters.value.rating || undefined
          },
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })
        if (response.data) {
          services.value = response.data
        }
      } catch (error) {
        console.error('Error fetching services:', error)
      } finally {
        loading.value = false
      }
    }

    const bookService = async (service) => {
      try {
        loading.value = true
        bookingService.value = service.id
        
        const response = await axios.post('/api/customers/requests', {
          service_id: service.id,
          remarks: ''
        })
        
        if (response.status === 201) {
          router.push({ 
            name: 'customer.requests',
            query: { booked: 'true' }
          })
        }
      } catch (error) {
        console.error('Error booking service:', error)
        alert('Failed to book service. Please try again.')
      } finally {
        loading.value = false
        bookingService.value = null
      }
    }

    const applyFilters = () => {
      fetchServices()
    }

    const resetFilters = () => {
      filters.value = {
        sortBy: 'name',
        minPrice: '',
        maxPrice: '',
        rating: '',
        search: ''
      }
      fetchServices()
    }

    const debouncedSearch = () => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => {
        applyFilters()
      }, 500)
    }

    const clearSearch = () => {
      filters.value.search = ''
      applyFilters()
    }

    let timeoutId

    onMounted(() => {
      fetchServices()
    })

    return {
      loading,
      services,
      serviceType,
      categories,
      filters,
      selectCategory,
      bookService,
      applyFilters,
      resetFilters,
      bookingService
    }
  }
}
</script>

<style scoped>
.filters-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  padding: 1.5rem;
}

.search-bar {
  position: relative;
  margin-bottom: 1.5rem;
}

.search-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #6c757d;
}

.search-input {
  padding-left: 2.5rem;
  padding-right: 2.5rem;
  height: 48px;
  border-radius: 8px;
  border: 1px solid #dee2e6;
  font-size: 1rem;
}

.search-input:focus {
  box-shadow: 0 0 0 3px rgba(13,110,253,0.15);
}

.clear-search {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
}

.advanced-filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  align-items: end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-label {
  font-size: 0.875rem;
  color: #6c757d;
  margin-bottom: 0.25rem;
}

.price-range .price-inputs {
  display: flex;
  gap: 0.5rem;
}

.price-inputs .input-group {
  flex: 1;
}

.reset-btn {
  height: 38px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  justify-content: center;
}

.reset-btn i {
  font-size: 1.1rem;
}

.rating span {
  font-size: 1.1rem;
}

.category-item {
  cursor: pointer;
  padding: 1rem;
  border-radius: 8px;
  transition: all 0.2s;
}

.category-item:hover, .category-item.active {
  background-color: #f8f9fa;
}

.category-icon {
  font-size: 2rem;
  color: #0d6efd;
}

.service-card {
  transition: transform 0.2s;
  border: 1px solid #dee2e6;
}

.service-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.price-tag {
  font-size: 1.25rem;
  font-weight: bold;
  color: #198754;
}
</style>