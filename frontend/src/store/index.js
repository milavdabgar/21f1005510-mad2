// src/store/index.js
import { createStore } from 'vuex'
import auth from './modules/auth'
import customer from './modules/customer'
import professional from './modules/professional'
import admin from './modules/admin'

export default createStore({
  modules: {
    auth,
    customer,
    professional,
    admin
  }
})
