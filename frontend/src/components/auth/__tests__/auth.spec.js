import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createStore } from 'vuex'
import LoginForm from '../LoginForm.vue'
import RegisterForm from '../RegisterForm.vue'
import { createRouter, createWebHistory } from 'vue-router'

// Mock store actions
const loginAction = vi.fn().mockImplementation(() => Promise.resolve())
const registerAction = vi.fn().mockImplementation(() => Promise.resolve())
const logoutAction = vi.fn()

// Mock store
const createMockStore = () => {
  return createStore({
    modules: {
      auth: {
        namespaced: true,
        state: {
          user: null,
          error: null,
          loading: false,
          message: null
        },
        getters: {
          authError: state => state.error,
          isLoading: state => state.loading,
          user: state => state.user,
          message: state => state.message
        },
        actions: {
          login: loginAction,
          register: registerAction,
          logout: logoutAction
        }
      }
    }
  })
}

// Mock router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: { template: '<div>Home</div>' }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: { template: '<div>Dashboard</div>' }
    },
    {
      path: '/login',
      name: 'login',
      component: { template: '<div>Login</div>' }
    },
    {
      path: '/register',
      name: 'register',
      component: { template: '<div>Register</div>' }
    }
  ]
})

describe('LoginForm', () => {
  let store
  let wrapper

  beforeEach(() => {
    // Reset mocks
    loginAction.mockClear()
    store = createMockStore()
    wrapper = mount(LoginForm, {
      global: {
        plugins: [store, router],
        stubs: {
          RouterLink: true
        }
      }
    })
  })

  it('renders login form', () => {
    expect(wrapper.find('[data-test="login-email"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="login-password"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="login-submit"]').exists()).toBe(true)
  })

  it('shows error message when login fails', async () => {
    store.state.auth.error = 'Invalid credentials'
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-test="error-message"]').text()).toBe('Invalid credentials')
  })

  it('shows pending approval message for pending professionals', async () => {
    store.state.auth.error = 'Your account is pending admin approval'
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-test="error-message"]').text()).toBe('Your account is pending admin approval')
  })

  it('shows rejection message for rejected professionals', async () => {
    store.state.auth.error = 'Your account has been rejected'
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-test="error-message"]').text()).toBe('Your account has been rejected')
  })

  it('calls login action on form submit', async () => {
    const email = 'test@scarlett.com'
    const password = 'test123'

    await wrapper.find('[data-test="login-email"]').setValue(email)
    await wrapper.find('[data-test="login-password"]').setValue(password)
    await wrapper.find('form').trigger('submit.prevent')

    expect(loginAction).toHaveBeenCalledWith(
      expect.anything(),
      { email, password }
    )
  })
})

describe('RegisterForm', () => {
  let store
  let wrapper

  beforeEach(() => {
    // Reset mocks
    registerAction.mockClear()
    store = createMockStore()
    wrapper = mount(RegisterForm, {
      global: {
        plugins: [store, router],
        stubs: {
          RouterLink: true
        }
      }
    })
  })

  it('renders register form', () => {
    expect(wrapper.find('[data-test="register-email"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="register-password"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="register-name"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="register-phone"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="register-type"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="register-submit"]').exists()).toBe(true)
  })

  it('shows professional fields when type is professional', async () => {
    await wrapper.find('[data-test="register-type"]').setValue('professional')
    expect(wrapper.find('[data-test="register-service-type"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="register-experience"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="id-proof-upload"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="certification-upload"]').exists()).toBe(true)
  })

  it('shows error message when registration fails', async () => {
    store.state.auth.error = 'Email already exists'
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-test="error-message"]').text()).toBe('Email already exists')
  })

  it('shows success message for professional registration', async () => {
    store.state.auth.message = 'Registration successful. Please wait for admin approval.'
    store.state.auth.user = { type: 'professional', status: 'pending' }
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-test="success-message"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="success-message"]').text()).toBe('Registration successful. Please wait for admin approval.')
  })

  it('calls register action on form submit', async () => {
    const formData = {
      email: 'test@scarlett.com',
      password: 'test123',
      name: 'Test User',
      phone: '1234567890',
      type: 'customer',
      address: '123 Test St',
      pincode: '123456'
    }

    await wrapper.find('[data-test="register-email"]').setValue(formData.email)
    await wrapper.find('[data-test="register-password"]').setValue(formData.password)
    await wrapper.find('[data-test="register-name"]').setValue(formData.name)
    await wrapper.find('[data-test="register-phone"]').setValue(formData.phone)
    await wrapper.find('[data-test="register-type"]').setValue(formData.type)
    await wrapper.find('[data-test="register-address"]').setValue(formData.address)
    await wrapper.find('[data-test="register-pincode"]').setValue(formData.pincode)
    await wrapper.find('form').trigger('submit.prevent')

    expect(registerAction).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining(formData)
    )
  })

  it('handles professional registration with documents', async () => {
    const formData = {
      email: 'professional@scarlett.com',
      password: 'test123',
      name: 'Test Professional',
      phone: '1234567890',
      type: 'professional',
      service_type: 'plumbing',
      experience: '5'
    }

    await wrapper.find('[data-test="register-type"]').setValue('professional')
    await wrapper.find('[data-test="register-email"]').setValue(formData.email)
    await wrapper.find('[data-test="register-password"]').setValue(formData.password)
    await wrapper.find('[data-test="register-name"]').setValue(formData.name)
    await wrapper.find('[data-test="register-phone"]').setValue(formData.phone)
    await wrapper.find('[data-test="register-service-type"]').setValue(formData.service_type)
    await wrapper.find('[data-test="register-experience"]').setValue(formData.experience)

    // Mock file uploads
    const idProof = new File(['test'], 'id.pdf', { type: 'application/pdf' })
    const certification = new File(['test'], 'cert.pdf', { type: 'application/pdf' })

    // Simulate file selection for both documents
    const idInput = wrapper.find('[data-test="id-proof-upload"]')
    Object.defineProperty(idInput.element, 'files', {
      value: [idProof]
    })
    await idInput.trigger('change')

    const certInput = wrapper.find('[data-test="certification-upload"]')
    Object.defineProperty(certInput.element, 'files', {
      value: [certification]
    })
    await certInput.trigger('change')

    await wrapper.find('form').trigger('submit.prevent')

    expect(registerAction).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({
        ...formData,
        id_proof: idProof,
        certification: certification
      })
    )
  })
})
