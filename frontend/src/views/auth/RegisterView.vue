<template>
  <div class="register-view">
    <div class="container">
      <RegisterForm />
    </div>
  </div>
</template>

<script>
import RegisterForm from '@/components/auth/RegisterForm.vue'

export default {
  name: 'RegisterView',
  components: {
    RegisterForm
  }
}
</script>

<style scoped>
.register-view {
  min-height: calc(100vh - var(--navbar-height));
  display: flex;
  align-items: center;
}
</style>
