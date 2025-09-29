// frontend/src/components/layout/Header.tsx - FIXED
import React from 'react';
import { useAuth } from '../../store/auth';
import { useIsOnline, useWsConnected, useAppStore } from '../../store/app';
import { cn } from '../../lib/utils';
import { ThemeToggleSimple } from '../../lib/theme';
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
  
  // Use individual selectors
  const toggleSidebar = useAppStore((state) => state.toggleSidebar);
  const setSettingsOpen = useAppStore((state) => state.setSettingsOpen);
  const isOnline = useIsOnline();
  const wsConnected = useWsConnected();
  
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
              <div className="flex items-center gap-1 text-yellow-600 dark:text-yellow-500" title="WebSocket disconnected">
                <WifiIcon className="w-4 h-4" />
                <span className="text-xs hidden sm:inline">Connecting...</span>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <ThemeToggleSimple />

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <BellIcon className="w-5 h-5" />
        </Button>

        {/* Settings */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSettingsOpen(true)}
          className="hidden md:flex"
        >
          <Cog6ToothIcon className="w-5 h-5" />
        </Button>

        {/* User avatar */}
        {user && (
          <Button
            variant="ghost"
            size="sm"
            className="gap-2"
            onClick={() => setSettingsOpen(true)}
          >
            <Avatar
              name={user.full_name || user.email}
              src={user.profile_picture}
              size="sm"
            />
            <span className="hidden lg:inline text-sm font-medium">
              {user.full_name || user.email.split('@')[0]}
            </span>
          </Button>
        )}
      </div>
    </header>
  );
}