// frontend/src/lib/config.ts

/**
 * Application-wide configuration constants
 */

// Environment configuration
export const config = {
  API_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  WS_URL: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/api/v1/chat/ws',
  ENVIRONMENT: (process.env.NODE_ENV as 'development' | 'production') || 'development',
  GOOGLE_CLIENT_ID: process.env.REACT_APP_GOOGLE_CLIENT_ID,
};

// API endpoints
export const endpoints = {
  // Auth
  auth: {
    google: `${config.API_URL}/auth/google/login`,
    googleCallback: `${config.API_URL}/auth/google/callback`,
    hubspot: `${config.API_URL}/auth/hubspot/login`,
    hubspotCallback: `${config.API_URL}/auth/hubspot/callback`,
    logout: `${config.API_URL}/auth/logout`,
    refresh: `${config.API_URL}/auth/refresh`,
  },
  
  // Chat
  chat: {
    stream: `${config.API_URL}/chat/stream`,
    history: `${config.API_URL}/chat/history`,
    clear: `${config.API_URL}/chat/history`,
    instructions: `${config.API_URL}/chat/instructions`,
    consent: `${config.API_URL}/chat/consent`,
    audit: `${config.API_URL}/chat/audit`,
  },
  
  // Profile
  profile: `${config.API_URL}/profile`,
  
  // Sync
  sync: {
    status: `${config.API_URL}/sync/status`,
    full: `${config.API_URL}/sync/full`,
    gmail: `${config.API_URL}/sync/gmail`,
    hubspot: `${config.API_URL}/sync/hubspot`,
    calendar: `${config.API_URL}/sync/calendar`,
  },
  
  // RAG
  rag: {
    search: `${config.API_URL}/rag/search`,
    documents: `${config.API_URL}/rag/documents`,
  },
  
  // Health
  health: `${config.API_URL}/health`,
} as const;

// App constants
export const constants = {
  // Chat configuration
  MAX_MESSAGE_LENGTH: 4000,
  MAX_MESSAGES_PER_THREAD: 100,
  TYPING_INDICATOR_DELAY: 500, // ms
  
  // File upload
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_FILE_TYPES: [
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
    'text/plain',
    'text/csv',
  ],
  
  // Pagination
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  
  // UI configuration
  SIDEBAR_WIDTH: 320,
  HEADER_HEIGHT: 56,
  MOBILE_BREAKPOINT: 768,
  
  // Animation durations (ms)
  ANIMATION_FAST: 150,
  ANIMATION_NORMAL: 300,
  ANIMATION_SLOW: 500,
  
  // Debounce/throttle delays (ms)
  DEBOUNCE_SEARCH: 300,
  DEBOUNCE_RESIZE: 150,
  THROTTLE_SCROLL: 100,
  
  // Session
  TOKEN_REFRESH_INTERVAL: 5 * 60 * 1000, // 5 minutes
  SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes
  
  // Date/Time formats
  DATE_FORMAT: 'MMM d, yyyy',
  TIME_FORMAT: 'h:mm a',
  DATETIME_FORMAT: 'MMM d, yyyy h:mm a',
  
  // Features flags
  FEATURES: {
    VOICE_INPUT: false,
    FILE_UPLOAD: false,
    EMOJI_REACTIONS: false,
    THREAD_SHARING: false,
    REAL_TIME_COLLABORATION: false,
  },
} as const;

// WebSocket configuration
export const wsConfig = {
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  pingInterval: 30000,
};

/**
 * Error messages
 */
export const errorMessages = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  AUTH_REQUIRED: 'Authentication required. Please log in.',
  TOKEN_EXPIRED: 'Your session has expired. Please log in again.',
  PERMISSION_DENIED: 'Permission denied.',
  NOT_FOUND: 'Resource not found.',
  VALIDATION_ERROR: 'Validation error. Please check your input.',
  SERVER_ERROR: 'Server error. Please try again later.',
  RATE_LIMIT: 'Too many requests. Please slow down.',
  MESSAGE_TOO_LONG: `Message is too long. Maximum ${constants.MAX_MESSAGE_LENGTH} characters.`,
  FILE_TOO_LARGE: `File is too large. Maximum ${constants.MAX_FILE_SIZE / 1024 / 1024}MB.`,
  INVALID_FILE_TYPE: 'Invalid file type.',
} as const;

/**
 * Success messages
 */
export const successMessages = {
  MESSAGE_SENT: 'Message sent successfully.',
  SAVED: 'Saved successfully.',
  DELETED: 'Deleted successfully.',
  COPIED: 'Copied to clipboard.',
  UPDATED: 'Updated successfully.',
  SYNCED: 'Synced successfully.',
} as const;


// Theme configuration
export const themeConfig = {
  storageKey: 'financial-advisor-theme',
  defaultTheme: 'system' as const,
} as const;

// WebSocket configuration
export const wsConfig = {
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000,
} as const;

// Error messages
export const errorMessages = {
  network: 'Network error. Please check your connection.',
  auth: 'Authentication failed. Please log in again.',
  sync: 'Sync failed. Please try again.',
  generic: 'Something went wrong. Please try again.',
} as const;

// Success messages
export const successMessages = {
  sync: 'Sync completed successfully',
  saved: 'Changes saved successfully',
  connected: 'Connected successfully',
} as const;