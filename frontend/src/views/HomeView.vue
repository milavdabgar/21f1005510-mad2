<template>
  <div class="home">
    <div class="container">
      <div class="row align-items-center min-vh-75">
        <div class="col-lg-6">
          <h1 class="display-4 fw-bold mb-4">Welcome to MAD2 Service App</h1>
          <p class="lead text-muted mb-4">
            Find professional services or offer your expertise.
            Join our community today!
          </p>
          <div class="d-grid gap-3 d-sm-flex">
            <router-link to="/register" class="btn btn-primary btn-lg px-4">
              Get Started
            </router-link>
            <router-link to="/login" class="btn btn-outline-primary btn-lg px-4">
              Login
            </router-link>
          </div>
        </div>
        <div class="col-lg-6 d-none d-lg-block">
          <img src="@/assets/service-illustration.svg" alt="Service Illustration" class="img-fluid">
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home {
  min-height: calc(100vh - var(--navbar-height));
  display: flex;
  align-items: center;
}
</style>
