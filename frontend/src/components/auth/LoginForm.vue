<template>
  <div class="login-form">
    <div class="card">
      <div class="card-body">
        <h2 class="text-center mb-4">Login</h2>
        
        <div v-if="error" class="alert alert-danger" role="alert">
          {{ error }}
        </div>
        
        <form @submit.prevent="handleSubmit">
          <div class="mb-3">
            <label for="email" class="form-label">Email</label>
            <input
              type="email"
              class="form-control"
              id="email"
              v-model="credentials.email"
              required
              @input="clearError"
            />
          </div>
          
          <div class="mb-3">
            <label for="password" class="form-label">Password</label>
            <input
              type="password"
              class="form-control"
              id="password"
              v-model="credentials.password"
              required
              @input="clearError"
            />
          </div>
          
          <button
            type="submit"
            class="btn btn-primary w-100"
            :disabled="loading"
          >
            {{ loading ? 'Logging in...' : 'Login' }}
          </button>
        </form>
        
        <div class="text-center mt-3">
          <router-link to="/register">Don't have an account? Register</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters, mapMutations } from 'vuex';
import { AUTH_MESSAGES } from '../../constants/messages';

export default {
  name: 'LoginForm',
  
  data() {
    return {
      credentials: {
        email: '',
        password: ''
      }
    };
  },
  
  computed: {
    ...mapGetters('auth', ['authError', 'isLoading']),
    error() {
      return this.authError;
    },
    loading() {
      return this.isLoading;
    }
  },
  
  methods: {
    ...mapActions('auth', ['login']),
    ...mapMutations('auth', ['clearError']),
    
    async handleSubmit() {
      console.log('Form submitted');
      
      // Clear any existing errors
      this.clearError();
      
      // Validate inputs
      if (!this.credentials.email || !this.credentials.password) {
        this.$store.commit('auth/setError', AUTH_MESSAGES.REQUIRED_FIELDS);
        return;
      }
      
      try {
        console.log('Attempting login...');
        await this.login(this.credentials);
        console.log('Login attempt completed');
      } catch (error) {
        console.error('Login component error:', error);
        // Error is now handled in the store, no need to do anything here
      }
    }
  },
  
  // Clear error when component is destroyed
  beforeDestroy() {
    this.clearError();
  }
};
</script>

<style scoped>
.login-form {
  max-width: 400px;
  margin: 2rem auto;
  padding: 1rem;
}

.card {
  border: none;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
}

.card-body {
  padding: 2rem;
}

.btn-primary {
  margin-top: 1rem;
}

.alert {
  margin-bottom: 1rem;
}
</style>
