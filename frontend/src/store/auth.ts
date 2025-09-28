// frontend/src/store/auth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, User, LoginResponse } from '../types';
import { storage } from '../lib/utils';

interface AuthStore extends AuthState {
  // Actions
  login: (response: LoginResponse) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
  setLoading: (loading: boolean) => void;
  clearError: () => void;
  
  // Auth helpers
  getAuthHeaders: () => Record<string, string>;
  isTokenValid: () => boolean;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      // Actions
      login: (response: LoginResponse) => {
        const { access_token, user } = response;
        
        set({
          user,
          token: access_token,
          isAuthenticated: true,
          isLoading: false,
        });
      },

      logout: () => {
        // Clear persisted state
        storage.remove('auth-storage');
        
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
        
        // Redirect to login
        window.location.href = '/';
      },

      updateUser: (userData: Partial<User>) => {
        const currentUser = get().user;
        if (currentUser) {
          set({
            user: { ...currentUser, ...userData }
          });
        }
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      clearError: () => {
        // Reserved for future error state
      },

      // Auth helpers
      getAuthHeaders: () => {
        const token = get().token;
        return token ? { Authorization: `Bearer ${token}` } : {};
      },

      isTokenValid: () => {
        const token = get().token;
        if (!token) return false;
        
        try {
          // Basic JWT validation (check if not expired)
          const payload = JSON.parse(atob(token.split('.')[1]));
          const now = Date.now() / 1000;
          return payload.exp > now;
        } catch (error) {
          console.warn('Invalid token format:', error);
          return false;
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Auth selectors for better performance
export const useAuth = () => useAuthStore((state) => ({
  user: state.user,
  isAuthenticated: state.isAuthenticated,
  isLoading: state.isLoading,
}));

export const useAuthActions = () => useAuthStore((state) => ({
  login: state.login,
  logout: state.logout,
  updateUser: state.updateUser,
  setLoading: state.setLoading,
}));

export const useAuthHeaders = () => useAuthStore((state) => state.getAuthHeaders());

// Hook to check if user is authenticated and token is valid
export const useIsAuthenticated = () => {
  return useAuthStore((state) => 
    state.isAuthenticated && state.isTokenValid()
  );
};