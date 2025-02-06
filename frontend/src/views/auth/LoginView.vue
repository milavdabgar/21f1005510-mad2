<template>
  <div class="login-view">
    <div class="container">
      <LoginForm />
    </div>
  </div>
</template>

<script>
import LoginForm from '@/components/auth/LoginForm.vue'

export default {
  name: 'LoginView',
  components: {
    LoginForm
  }
}
</script>

<style scoped>
.login-view {
  min-height: calc(100vh - var(--navbar-height));
  display: flex;
  align-items: center;
}
</style>
