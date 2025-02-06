<template>
  <span :class="statusClass">
    {{ formattedStatus }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

const statusClass = computed(() => {
  const classes = {
    'requested': 'badge bg-warning',
    'assigned': 'badge bg-primary',
    'in_progress': 'badge bg-info',
    'completed': 'badge bg-success',
    'cancelled': 'badge bg-danger'
  }
  return classes[props.status] || 'badge bg-secondary'
})

const formattedStatus = computed(() => {
  return props.status.replace('_', ' ').charAt(0).toUpperCase() + 
         props.status.slice(1).replace('_', ' ')
})
</script>

<style scoped>
.badge {
  font-size: 0.875rem;
  padding: 0.35em 0.65em;
  font-weight: 500;
}
</style>
