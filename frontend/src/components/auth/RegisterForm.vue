<template>
  <div class="register-view">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-12 col-md-10 col-lg-8 col-xl-6">
          <div class="auth-card">
            <div class="text-center mb-4">
              <h1 class="h3 mb-3">Create Account</h1>
              <p class="text-muted">Join our community today</p>
            </div>

            <form @submit.prevent="handleSubmit">
              <div class="form-floating mb-3">
                <select
                  class="form-select"
                  id="type"
                  v-model="formData.type"
                  required
                >
                  <option value="">Select account type</option>
                  <option value="professional">Professional</option>
                  <option value="customer">Customer</option>
                </select>
                <label for="type">Account Type</label>
              </div>

              <div class="form-floating mb-3">
                <input
                  type="email"
                  class="form-control"
                  id="email"
                  placeholder="name@scarlett.com"
                  v-model="formData.email"
                  required
                >
                <label for="email">Email address</label>
              </div>

              <div class="form-floating mb-3">
                <input
                  type="text"
                  class="form-control"
                  id="name"
                  placeholder="John Doe"
                  v-model="formData.name"
                  required
                >
                <label for="name">Full Name</label>
              </div>

              <div class="form-floating mb-3">
                <input
                  type="tel"
                  class="form-control"
                  id="phone"
                  placeholder="Phone number"
                  v-model="formData.phone"
                  required
                >
                <label for="phone">Phone Number</label>
              </div>

              <div class="form-floating mb-3">
                <input
                  type="password"
                  class="form-control"
                  id="password"
                  placeholder="Password"
                  v-model="formData.password"
                  required
                >
                <label for="password">Password</label>
              </div>

              <!-- Customer specific fields -->
              <template v-if="formData.type === 'customer'">
                <div class="form-floating mb-3">
                  <textarea
                    class="form-control"
                    id="address"
                    placeholder="Your address"
                    v-model="formData.address"
                    style="height: 100px"
                    required
                  ></textarea>
                  <label for="address">Address</label>
                </div>

                <div class="form-floating mb-4">
                  <input
                    type="text"
                    class="form-control"
                    id="pincode"
                    placeholder="Pincode"
                    v-model="formData.pincode"
                    required
                  >
                  <label for="pincode">Pincode</label>
                </div>
              </template>

              <!-- Professional specific fields -->
              <template v-if="formData.type === 'professional'">
                <div class="form-floating mb-3">
                  <select
                    class="form-select"
                    id="serviceType"
                    v-model="formData.service_type"
                    required
                  >
                    <option value="">Select service type</option>
                    <option value="plumber">Plumber</option>
                    <option value="electrician">Electrician</option>
                    <option value="carpenter">Carpenter</option>
                    <option value="painter">Painter</option>
                  </select>
                  <label for="serviceType">Service Type</label>
                </div>

                <div class="form-floating mb-3">
                  <input
                    type="number"
                    class="form-control"
                    id="experience"
                    placeholder="Years of experience"
                    v-model="formData.experience"
                    min="0"
                    required
                  >
                  <label for="experience">Years of Experience</label>
                </div>

                <div class="mb-3">
                  <label for="idProof" class="form-label">ID Proof</label>
                  <input
                    type="file"
                    class="form-control"
                    id="idProof"
                    @change="handleFileUpload($event, 'id_proof')"
                    accept=".pdf,.jpg,.jpeg,.png"
                    required
                  >
                  <div class="form-text">Upload a valid government ID proof</div>
                </div>

                <div class="mb-4">
                  <label for="certification" class="form-label">Certification</label>
                  <input
                    type="file"
                    class="form-control"
                    id="certification"
                    @change="handleFileUpload($event, 'certification')"
                    accept=".pdf,.jpg,.jpeg,.png"
                    required
                  >
                  <div class="form-text">Upload your professional certification</div>
                </div>
              </template>

              <div class="alert alert-danger" v-if="error">
                {{ error }}
              </div>

              <div class="alert alert-success" v-if="message">
                {{ message }}
              </div>

              <div class="d-grid mb-4">
                <button
                  type="submit"
                  class="btn btn-primary btn-lg"
                  :disabled="loading"
                >
                  <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                  Create Account
                </button>
              </div>

              <p class="text-center mb-0">
                Already have an account?
                <router-link to="/login" class="text-decoration-none">
                  Sign in
                </router-link>
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'RegisterForm',
  setup() {
    const store = useStore()
    const router = useRouter()

    const formData = ref({
      type: '',
      email: '',
      name: '',
      phone: '',
      password: '',
      address: '',
      pincode: '',
      service_type: '',
      experience: '',
      id_proof: null,
      certification: null
    })

    const loading = computed(() => store.getters['auth/isLoading'])
    const error = computed(() => store.getters['auth/authError'])
    const message = computed(() => store.getters['auth/message'])

    const handleFileUpload = (event, field) => {
      formData.value[field] = event.target.files[0]
    }

    const handleSubmit = async () => {
      try {
        const response = await store.dispatch('auth/register', formData.value)

        if (formData.value.type === 'customer') {
          // Customers are automatically logged in
          router.push('/')
        } else {
          // Professionals need admin approval
          setTimeout(() => {
            router.push('/login')
          }, 3000)
        }
      } catch (error) {
        // Error is handled by the store
        console.error('Registration failed:', error)
      }
    }

    return {
      formData,
      loading,
      error,
      message,
      handleFileUpload,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.auth-card {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
}

.form-text {
  font-size: 0.875rem;
  color: #6c757d;
}
</style>
