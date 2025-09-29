// frontend/src/store/app.ts - PERMANENT FIX
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AppSettings, SyncStatus } from '../types';

interface AppState {
  // UI State
  sidebarOpen: boolean;
  settingsOpen: boolean;
  commandPaletteOpen: boolean;
  
  // App Settings
  settings: AppSettings;
  
  // Sync Status
  syncStatus: SyncStatus;
  
  // Connection State
  isOnline: boolean;
  wsConnected: boolean;
  
  // Notifications
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message?: string;
    timestamp: string;
    read: boolean;
  }>;
}

interface AppActions {
  // UI Actions
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setSettingsOpen: (open: boolean) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  
  // Settings Actions
  updateSettings: (settings: Partial<AppSettings>) => void;
  resetSettings: () => void;
  
  // Sync Actions
  updateSyncStatus: (status: Partial<SyncStatus>) => void;
  
  // Connection Actions
  setOnlineStatus: (online: boolean) => void;
  setWebSocketStatus: (connected: boolean) => void;
  
  // Notification Actions
  addNotification: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp' | 'read'>) => void;
  markNotificationRead: (id: string) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

type AppStore = AppState & AppActions;

const defaultSettings: AppSettings = {
  theme: 'system',
  notifications: {
    email: true,
    push: true,
    sound: false,
  },
  privacy: {
    data_sharing: false,
    analytics: true,
  },
};

const defaultSyncStatus: SyncStatus = {
  gmail: {
    connected: false,
    last_sync: null,
    status: 'idle',
    total_emails: 0,
  },
  hubspot: {
    connected: false,
    last_sync: null,
    status: 'idle',
    total_contacts: 0,
  },
  calendar: {
    connected: false,
    last_sync: null,
    status: 'idle',
    total_events: 0,
  },
};

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      // Initial state
      sidebarOpen: true,
      settingsOpen: false,
      commandPaletteOpen: false,
      settings: defaultSettings,
      syncStatus: defaultSyncStatus,
      isOnline: navigator.onLine,
      wsConnected: false,
      notifications: [],

      // UI Actions
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      
      setSettingsOpen: (open) => set({ settingsOpen: open }),
      
      setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),

      // Settings Actions
      updateSettings: (newSettings) => set((state) => ({
        settings: { ...state.settings, ...newSettings }
      })),

      resetSettings: () => set({ settings: defaultSettings }),

      // Sync Actions
      updateSyncStatus: (statusUpdate) => set((state) => ({
        syncStatus: { ...state.syncStatus, ...statusUpdate }
      })),

      // Connection Actions
      setOnlineStatus: (online) => set({ isOnline: online }),
      
      setWebSocketStatus: (connected) => set({ wsConnected: connected }),

      // Notification Actions
      addNotification: (notification) => set((state) => {
        const newNotification = {
          ...notification,
          id: Math.random().toString(36).substring(2),
          timestamp: new Date().toISOString(),
          read: false,
        };
        
        return {
          notifications: [newNotification, ...state.notifications].slice(0, 50)
        };
      }),

      markNotificationRead: (id) => set((state) => ({
        notifications: state.notifications.map((notif) =>
          notif.id === id ? { ...notif, read: true } : notif
        )
      })),

      removeNotification: (id) => set((state) => ({
        notifications: state.notifications.filter((notif) => notif.id !== id)
      })),

      clearNotifications: () => set({ notifications: [] }),
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        settings: state.settings,
      }),
    }
  )
);

// ✅ FIXED: Simple direct selectors - no object creation
export const useSidebarOpen = () => useAppStore((state) => state.sidebarOpen);
export const useSettingsOpen = () => useAppStore((state) => state.settingsOpen);
export const useSettings = () => useAppStore((state) => state.settings);
export const useSyncStatus = () => useAppStore((state) => state.syncStatus);
export const useIsOnline = () => useAppStore((state) => state.isOnline);
export const useWsConnected = () => useAppStore((state) => state.wsConnected);
export const useNotifications = () => useAppStore((state) => state.notifications);

// ✅ FIXED: Action selectors - directly return functions
export const useSyncActions = () => useAppStore((state) => state.updateSyncStatus);