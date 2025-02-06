<script setup>
import { RouterView } from 'vue-router'
import { computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import Navbar from '@/components/layout/Navbar.vue'

const store = useStore()

// Load user profile if token exists
onMounted(async () => {
  await store.dispatch('auth/initialize')
})
</script>

<template>
  <div class="app" id="app">
    <Navbar />
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style>
.main-content {
  padding-top: 4rem;
  min-height: 100vh;
}

#app {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", "Noto Sans", "Liberation Sans", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>