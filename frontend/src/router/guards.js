import store from '../store';

export function authGuard(to, from, next) {
  if (store.getters['auth/isAuthenticated']) {
    next();
  } else {
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    });
  }
}

export function guestGuard(to, from, next) {
  if (!store.getters['auth/isAuthenticated']) {
    next();
  } else {
    next('/dashboard');
  }
}
