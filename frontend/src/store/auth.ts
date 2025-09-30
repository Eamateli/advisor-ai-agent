// frontend/src/store/auth.ts - COMPLETE & CORRECT
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, LoginResponse } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isLoggingOut: boolean;
}

interface AuthActions {
  login: (response: LoginResponse) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
  setLoading: (loading: boolean) => void;
  isTokenValid: () => boolean;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      isLoggingOut: false,

      // Actions
      login: (response: LoginResponse) => {
        const { access_token, user } = response;
        
        set({
          user,
          token: access_token,
          isAuthenticated: true,
          isLoading: false,
        });

        // Store token in memory only (not localStorage for security)
        // The token will be automatically included in API requests via interceptors
        // localStorage.setItem('access_token', access_token); // REMOVED FOR SECURITY
      },

      logout: () => {
        // Set logout flag to prevent any API calls
        set({ isLoggingOut: true });
        
        // Note: Token is no longer stored in localStorage for security
        // localStorage.removeItem('auth-storage');
        // localStorage.removeItem('access_token');
        
        // Clear state but keep isLoggingOut true for a moment
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
        
        // Reset logout flag after a short delay to allow API calls to complete
        setTimeout(() => {
          set({ isLoggingOut: false });
        }, 1000);
        
        // Don't force page reload - let the component handle navigation
        // window.location.href = '/login';
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

      isTokenValid: () => {
        const token = get().token;
        if (!token) return false;
        
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          const now = Date.now() / 1000;
          return payload.exp > (now + 300);
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

// Simple selectors that don't create objects
export const useAuth = () => useAuthStore((state) => ({
  user: state.user,
  isAuthenticated: state.isAuthenticated,
  isLoading: state.isLoading,
  token: state.token,
}));

export const useAuthActions = () => useAuthStore((state) => ({
  login: state.login,
  logout: state.logout,
  updateUser: state.updateUser,
  setLoading: state.setLoading,
}));