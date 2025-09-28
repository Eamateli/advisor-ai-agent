// frontend/src/services/api.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { config, endpoints } from '../lib/config';
import { useAuthStore } from '../store/auth';
import { parseErrorMessage } from '../lib/utils';
import toast from 'react-hot-toast';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: config.API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth headers
    this.client.interceptors.request.use(
      (config) => {
        const authStore = useAuthStore.getState();
        const token = authStore.token;
        
        if (token && authStore.isTokenValid()) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 errors (unauthorized)
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          // Try to refresh token or logout
          const authStore = useAuthStore.getState();
          if (!authStore.isTokenValid()) {
            authStore.logout();
            toast.error('Session expired. Please log in again.');
            return Promise.reject(error);
          }
        }

        // Handle rate limiting
        if (error.response?.status === 429) {
          const retryAfter = error.response.headers['retry-after'];
          toast.error(`Rate limit exceeded. Try again in ${retryAfter || 60} seconds.`);
        }

        // Handle network errors
        if (!error.response) {
          toast.error('Network error. Please check your connection.');
        }

        return Promise.reject(error);
      }
    );
  }

  // Generic request method
  async request<T = any>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.request(config);
      return response.data;
    } catch (error) {
      const errorMessage = parseErrorMessage(error);
      throw new Error(errorMessage);
    }
  }

  // HTTP methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'GET', url });
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'POST', url, data });
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PUT', url, data });
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PATCH', url, data });
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'DELETE', url });
  }

  // Stream method for Server-Sent Events
  async stream(url: string, config?: AxiosRequestConfig): Promise<ReadableStream> {
    const authStore = useAuthStore.getState();
    const headers = {
      ...config?.headers,
      ...(authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {}),
    };

    const response = await fetch(`${config.API_URL}${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: JSON.stringify(config?.data || {}),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('No response body available for streaming');
    }

    return response.body;
  }
}

// Create singleton instance
export const api = new ApiClient();

// Typed API endpoints
export const authApi = {
  googleLogin: () => api.get(endpoints.auth.google),
  hubspotLogin: () => api.get(endpoints.auth.hubspot),
  logout: () => api.post(endpoints.auth.logout),
};

export const chatApi = {
  sendMessage: (message: string, conversation_id?: string) =>
    api.post(endpoints.chat.stream, { message, conversation_id }),
  
  getHistory: (limit = 50, offset = 0) =>
    api.get(`${endpoints.chat.history}?limit=${limit}&offset=${offset}`),
  
  clearHistory: () => api.delete(endpoints.chat.clear),
  
  getInstructions: () => api.get(endpoints.chat.instructions),
  
  updateInstructions: (instructions: string) =>
    api.patch(endpoints.chat.instructions, { instructions }),
  
  grantConsent: (action_type: string, scope = 'all', conditions?: any) =>
    api.post(`${endpoints.chat.consent}/grant`, { action_type, scope, conditions }),
  
  revokeConsent: (action_type: string) =>
    api.post(`${endpoints.chat.consent}/revoke/${action_type}`),
  
  getConsents: () => api.get(endpoints.chat.consent),
  
  getAuditLogs: (limit = 20, offset = 0) =>
    api.get(`${endpoints.chat.audit}?limit=${limit}&offset=${offset}`),
};

export const profileApi = {
  get: () => api.get(endpoints.profile),
  update: (data: any) => api.patch(endpoints.profile, data),
};

export const syncApi = {
  getStatus: () => api.get(endpoints.sync.status),
  
  triggerFullSync: (options: {
    days_back?: number;
    include_gmail?: boolean;
    include_hubspot?: boolean;
    include_calendar?: boolean;
  }) => api.post(endpoints.sync.full, options),
  
  syncGmail: (days_back = 30) =>
    api.post(endpoints.sync.gmail, { days_back }),
  
  syncHubspot: () => api.post(endpoints.sync.hubspot),
  
  syncCalendar: (days_back = 30, days_forward = 90) =>
    api.post(endpoints.sync.calendar, { days_back, days_forward }),
};

export const ragApi = {
  search: (query: string, limit = 10) =>
    api.post(endpoints.rag.search, { query, limit }),
  
  getDocuments: (limit = 20, offset = 0, doc_type?: string) =>
    api.get(`${endpoints.rag.documents}?limit=${limit}&offset=${offset}${doc_type ? `&doc_type=${doc_type}` : ''}`),
};

export const healthApi = {
  check: () => api.get(endpoints.health),
};

export default api;