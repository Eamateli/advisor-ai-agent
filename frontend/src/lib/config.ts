// frontend/src/lib/config.ts
import { Config } from '../types';

// Environment configuration with validation
function getEnvVar(name: string, defaultValue?: string): string {
  const value = process.env[name] || defaultValue;
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export const config: Config = {
  API_URL: getEnvVar('REACT_APP_API_URL', 'http://localhost:8000/api/v1'),
  WS_URL: getEnvVar('REACT_APP_WS_URL', 'ws://localhost:8000/api/v1/chat/ws'),
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

// WebSocket configuration
export const wsConfig = {
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  pingInterval: 30000,
};

// App constants
export const constants = {
  MAX_MESSAGE_LENGTH: 4000,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  SUPPORTED_FILE_TYPES: ['text/plain', 'application/pdf', 'text/csv'],
  PAGINATION_SIZE: 20,
  DEBOUNCE_DELAY: 300,
  ANIMATION_DURATION: 200,
  TOAST_DURATION: 4000,
} as const;

// Feature flags
export const features = {
  DARK_MODE: true,
  WEBSOCKETS: true,
  FILE_UPLOAD: true,
  VOICE_INPUT: false, // Future feature
  EXPORT_CHAT: true,
  ANALYTICS: config.ENVIRONMENT === 'production',
} as const;

// Theme configuration
export const themeConfig = {
  defaultTheme: 'system' as const,
  storageKey: 'fa-theme',
  attribute: 'class',
  enableSystem: true,
};

// Validation helpers
export const validateConfig = () => {
  const required = ['API_URL', 'WS_URL'];
  const missing = required.filter(key => !config[key as keyof Config]);
  
  if (missing.length > 0) {
    throw new Error(`Missing required configuration: ${missing.join(', ')}`);
  }
  
  // Validate URLs
  try {
    new URL(config.API_URL);
    new URL(config.WS_URL.replace('ws', 'http'));
  } catch (error) {
    throw new Error('Invalid API or WebSocket URL configuration');
  }
};

// Initialize and validate config
validateConfig();