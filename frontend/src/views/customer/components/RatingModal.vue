<template>
  <div 
    class="modal fade show" 
    style="display: block"
    @click.self="$emit('close')"
  >
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ readOnly ? 'View Rating' : 'Rate Service' }}</h5>
          <button 
            type="button" 
            class="btn-close"
            @click="$emit('close')"
          ></button>
        </div>
        
        <div class="modal-body">
          <div class="mb-3">
            <label class="form-label">Rating</label>
            <div class="rating-stars">
              <template v-for="i in 5" :key="i">
                <span 
                  class="star"
                  :class="{
                    'filled': i <= rating,
                    'clickable': !readOnly
                  }"
                  @click="setRating(i)"
                >★</span>
              </template>
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label">Review</label>
            <textarea 
              class="form-control"
              v-model="review"
              :readonly="readOnly"
              :disabled="readOnly"
              rows="3"
              placeholder="Tell us about your experience..."
            ></textarea>
          </div>

          <div v-if="error" class="alert alert-danger">
            {{ error }}
          </div>
        </div>

        <div class="modal-footer">
          <button 
            type="button" 
            class="btn btn-secondary"
            @click="$emit('close')"
          >
            Close
          </button>
          <button 
            v-if="!readOnly"
            type="button"
            class="btn btn-primary"
            :disabled="submitting"
            @click="submitRating"
          >
            {{ submitting ? 'Submitting...' : 'Submit Rating' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal backdrop -->
  <div class="modal-backdrop fade show"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { CustomerService } from '@/services/customer'

const props = defineProps({
  requestId: {
    type: Number,
    required: true
  },
  readOnly: {
    type: Boolean,
    default: false
  },
  initialRating: {
    type: Number,
    default: 0
  },
  initialRemarks: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close', 'rated'])

const rating = ref(props.initialRating)
const review = ref(props.initialRemarks)
const submitting = ref(false)
const error = ref(null)

const handleEscKey = (event) => {
  if (event.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscKey)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleEscKey)
})

const setRating = (value) => {
  if (!props.readOnly) {
    rating.value = value
  }
}

const submitRating = async () => {
  if (props.readOnly) {
    emit('close')
    return
  }

  if (!rating.value) {
    error.value = 'Please select a rating'
    return
  }

  submitting.value = true
  error.value = null

  try {
    await CustomerService.rateRequest(props.requestId, {
      rating: rating.value,
      remarks: review.value
    })
    emit('rated')
  } catch (err) {
    error.value = err.message || 'Failed to submit rating'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.modal {
  background: rgba(0, 0, 0, 0.5);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1050;
}

.modal-backdrop {
  z-index: 1040;
}

.rating-stars {
  font-size: 24px;
  user-select: none;
}

.star {
  color: #ccc;
  margin-right: 5px;
  cursor: default;
}

.star.filled {
  color: #ffc107;
}

.star.clickable {
  cursor: pointer;
}

.star.clickable:hover {
  color: #ffc107;
}

textarea[readonly] {
  background-color: #f8f9fa;
  cursor: default;
}
</style>
