import store from '../store';
import router from '../router';

export default async function authMiddleware(to, from, next) {
  // Check if route requires authentication
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin);
  const requiresProfessional = to.matched.some(record => record.meta.requiresProfessional);
  const requiresCustomer = to.matched.some(record => record.meta.requiresCustomer);
  
  // If no authentication is required, proceed
  if (!requiresAuth && !requiresAdmin && !requiresProfessional && !requiresCustomer) {
    return next();
  }
  
  // Check if user is authenticated
  const isAuthenticated = store.getters['auth/isAuthenticated'];
  if (!isAuthenticated) {
    return next({ name: 'login', query: { redirect: to.fullPath } });
  }
  
  // Fetch user profile if not available
  if (!store.getters['auth/currentUser']) {
    await store.dispatch('auth/fetchProfile');
  }
  
  // Check role-based access
  const isAdmin = store.getters['auth/isAdmin'];
  const isProfessional = store.getters['auth/isProfessional'];
  const isCustomer = store.getters['auth/isCustomer'];
  
  if (requiresAdmin && !isAdmin) {
    return next({ name: 'unauthorized' });
  }
  
  if (requiresProfessional && !isProfessional) {
    return next({ name: 'unauthorized' });
  }
  
  if (requiresCustomer && !isCustomer) {
    return next({ name: 'unauthorized' });
  }
  
  next();
}
