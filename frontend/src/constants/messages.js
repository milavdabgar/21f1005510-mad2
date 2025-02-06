export const AUTH_MESSAGES = {
  // Success messages
  REGISTRATION_SUCCESS: 'Registration successful! You can now log in.',
  PROFESSIONAL_REGISTRATION_SUCCESS: 'Registration successful. Please wait for admin approval.',
  LOGIN_SUCCESS: 'Login successful!',
  PROFILE_UPDATE_SUCCESS: 'Profile updated successfully',
  
  // Error messages
  REGISTRATION_FAILED: 'Registration failed. Please try again.',
  LOGIN_FAILED: 'Invalid email or password.',
  INVALID_CREDENTIALS: 'Invalid email or password',
  ACCOUNT_PENDING: 'Your account is pending approval. Please wait for admin confirmation.',
  ACCOUNT_REJECTED: 'Your account has been rejected. Please contact support.',
  ACCOUNT_BLOCKED: 'Your account has been blocked. Please contact support.',
  ACCOUNT_INACTIVE: 'Your account has been deactivated',
  NETWORK_ERROR: 'Network error. Please check your connection.',
  SERVER_ERROR: 'Server error. Please try again later.',
  UNAUTHORIZED: 'You are not authorized to access this resource.',
  SESSION_EXPIRED: 'Your session has expired. Please log in again.',
  
  // Validation messages
  REQUIRED_FIELDS: 'Please fill in all required fields.',
  INVALID_EMAIL: 'Please enter a valid email address.',
  PASSWORD_LENGTH: 'Password must be at least 6 characters long',
  DOCUMENT_REQUIRED: 'Please upload all required documents',
  INVALID_FILE_TYPE: 'Only PDF, JPG, JPEG, and PNG files are allowed',
  
  // Admin messages
  PROFESSIONAL_APPROVED: 'Professional approved successfully',
  PROFESSIONAL_REJECTED: 'Professional rejected successfully',
  USER_BLOCKED: 'User blocked successfully',
  USER_UNBLOCKED: 'User unblocked successfully'
};
