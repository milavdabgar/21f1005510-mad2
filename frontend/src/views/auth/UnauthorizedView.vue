<template>
  <div class="unauthorized">
    <div class="text-center">
      <h1 class="display-4">Access Denied</h1>
      <p class="lead">You don't have permission to access this page.</p>
      <router-link to="/" class="btn btn-primary">Go Home</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UnauthorizedView'
}
</script>

<style scoped>
.unauthorized {
  padding: 4rem 1rem;
  max-width: 600px;
  margin: 0 auto;
}
</style>
