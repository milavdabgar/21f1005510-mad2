import './assets/main.css'
import './assets/base.css'
import './assets/components.css'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

// Import Vue Toastification
import Toast from "vue-toastification"
import "vue-toastification/dist/index.css"

const app = createApp(App)

// Configure toast options
const toastOptions = {
    position: "top-right",
    timeout: 3000,
    closeOnClick: true,
    pauseOnFocusLoss: true,
    pauseOnHover: true,
    draggable: true,
    draggablePercent: 0.6,
    showCloseButtonOnHover: false,
    hideProgressBar: true,
    closeButton: "button",
    icon: true,
    rtl: false
}

app.use(router)
app.use(store)
app.use(Toast, toastOptions)

app.mount('#app')
