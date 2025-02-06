<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm fixed-top">
    <div class="container">
      <router-link
        class="navbar-brand fw-bold text-primary"
        :to="getDashboardRoute"
      >
        A-Z Services
      </router-link>

      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse justify-content-end" id="navbarNav">
        <ul class="navbar-nav">
          <template v-if="isAuthenticated">
            <!-- Customer Navigation -->
            <template v-if="isCustomer">
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'customer.dashboard' }"
                >
                  Dashboard
                </router-link>
              </li>
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'customer.services' }"
                >
                  Services
                </router-link>
              </li>
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'customer.requests' }"
                >
                  My Bookings
                </router-link>
              </li>
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'customer.summary' }"
                >
                  Summary
                </router-link>
              </li>
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'customer.profile' }"
                >
                  Profile
                </router-link>
              </li>
            </template>

            <!-- Professional Navigation -->
            <template v-if="isProfessional">
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'professional.dashboard' }"
                >
                  Dashboard
                </router-link>
              </li>
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'professional.profile' }"
                >
                  Profile
                </router-link>
              </li>
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'professional.summary' }"
                >
                  Summary
                </router-link>
              </li>
            </template>

            <!-- Admin Navigation -->
            <template v-if="isAdmin">
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'admin-dashboard' }"
                >
                  Dashboard
                </router-link>
              </li>
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'admin-services' }"
                >
                  Services
                </router-link>
              </li>
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'admin-professionals' }"
                >
                  Professionals
                </router-link>
              </li>
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'admin-customers' }"
                >
                  Customers
                </router-link>
              </li>
              <li class="nav-item">
                <router-link
                  class="nav-link px-3"
                  :to="{ name: 'admin-requests' }"
                >
                  Requests
                </router-link>
              </li>
            </template>

            <!-- Common Navigation for Authenticated Users -->
            <li class="nav-item">
              <a class="nav-link px-3" href="#" @click.prevent="logout">
                Logout
              </a>
            </li>
          </template>

          <!-- Guest Navigation -->
          <template v-else>
            <li class="nav-item">
              <router-link class="nav-link px-3" to="/login">
                Login
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link px-3" to="/register">
                Register
              </router-link>
            </li>
          </template>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

const store = useStore()
const router = useRouter()

const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])
const userType = computed(() => store.getters['auth/userType'])
const isCustomer = computed(() => userType.value === 'customer')
const isProfessional = computed(() => userType.value === 'professional')
const isAdmin = computed(() => userType.value === 'admin')

const getDashboardRoute = computed(() => {
  if (!isAuthenticated.value) return '/'
  switch (userType.value) {
    case 'customer':
      return '/customer/dashboard'
    case 'professional':
      return '/professional/dashboard'
    case 'admin':
      return '/admin'
    default:
      return '/'
  }
})

const logout = async () => {
  await store.dispatch('auth/logout')
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  margin-bottom: 2rem;
}

.nav-link {
  cursor: pointer;
}

.nav-link.active {
  font-weight: bold;
  color: var(--bs-primary) !important;
}
</style>