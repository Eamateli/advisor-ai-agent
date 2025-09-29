// frontend/src/components/layout/Header.tsx
import React from 'react';
import { useAuth } from '../../store/auth';
import { useAppStore } from '../../store/app';
import { useConnectionStatus } from '../../store/app';
import { cn } from '../../lib/utils';
import { ThemeToggle } from '../../lib/theme';
import { Button } from '../ui/Button';
import { Avatar } from '../ui/Avatar';
import { 
  Bars3Icon,
  Cog6ToothIcon,
  BellIcon,
  WifiIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';

export function Header() {
  const { user } = useAuth();
  const toggleSidebar = useAppStore((state) => state.toggleSidebar);
  const setSettingsOpen = useAppStore((state) => state.setSettingsOpen);
  const isOnline = useAppStore((state) => state.isOnline);
  const wsConnected = useAppStore((state) => state.wsConnected);
  return (
    <header className="flex items-center justify-between h-14 px-4 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      {/* Left section */}
      <div className="flex items-center gap-3">
        {/* Sidebar toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="md:hidden"
        >
          <Bars3Icon className="w-5 h-5" />
        </Button>

        {/* App title */}
        <div className="hidden md:flex items-center gap-2">
          <h1 className="text-lg font-semibold text-foreground">
            Ask Anything
          </h1>
          
          {/* Connection status indicator */}
          <div className="flex items-center gap-1">
            {!isOnline ? (
              <div className="flex items-center gap-1 text-destructive" title="No internet connection">
                <ExclamationTriangleIcon className="w-4 h-4" />
                <span className="text-xs hidden sm:inline">Offline</span>
              </div>
            ) : !wsConnected ? (
              <div className="flex items-center gap-1 text-yellow-600" title="Connecting...">
                <WifiIcon className="w-4 h-4" />
                <span className="text-xs hidden sm:inline">Connecting</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-green-600" title="Connected">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-xs hidden sm:inline">Live</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Center section - Context indicator */}
      <div className="hidden md:flex items-center gap-2 text-sm text-muted-foreground">
        <span>Context set to all meetings</span>
        <span className="text-xs">11/7am - May 13, 2025</span>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-2">
        {/* Notifications */}
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          title="Notifications"
        >
          <BellIcon className="w-5 h-5" />
          {/* Notification badge (if any) */}
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-destructive rounded-full" />
        </Button>

        {/* Theme toggle */}
        <ThemeToggle />

        {/* Settings */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSettingsOpen(true)}
          title="Settings"
        >
          <Cog6ToothIcon className="w-5 h-5" />
        </Button>

        {/* User profile */}
        <Button
          variant="ghost"
          className="flex items-center gap-2 h-8 px-2"
          title="Profile"
        >
          <Avatar
            src={user?.profile_picture}
            name={user?.full_name || user?.email || 'User'}
            size="sm"
          />
          <span className="hidden sm:inline text-sm font-medium">
            {user?.full_name || user?.email?.split('@')[0]}
          </span>
        </Button>
      </div>
    </header>
  );
}