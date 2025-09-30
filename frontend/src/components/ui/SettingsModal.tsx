// frontend/src/components/ui/SettingsModal.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, useAuthActions } from '../../store/auth';
import { useAppStore } from '../../store/app';
import { wsService } from '../../services/websocket';
import { Button } from './Button';
import { Avatar } from './Avatar';
import { 
  XMarkIcon,
  UserIcon,
  BellIcon,
  ShieldCheckIcon,
  KeyIcon,
  ArrowRightOnRectangleIcon,
  Cog6ToothIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';
import toast from 'react-hot-toast';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { user } = useAuth();
  const { logout } = useAuthActions();
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    
    // Clear any existing toasts first
    toast.dismiss();
    
    try {
      // Disconnect WebSocket first to prevent ongoing requests
      wsService.disconnect();
      
      // Clear client state
      logout();
      
      // Close modal and navigate
      onClose();
      navigate('/login');
    } catch (error) {
      // Even if something fails, we've already cleared the state
      console.error('Logout error:', error);
      onClose();
      navigate('/login');
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleNavigateToSettings = () => {
    onClose();
    navigate('/settings');
  };

  const handleNavigateToSettingsTab = (tab: string) => {
    onClose();
    navigate(`/settings?tab=${tab}`);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-card border border-border rounded-lg shadow-lg w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">Settings</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="w-8 h-8"
          >
            <XMarkIcon className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* User Profile */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
            <Avatar
              name={user?.full_name || user?.email || 'User'}
              src={user?.profile_picture}
              size="md"
            />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-foreground truncate">
                {user?.full_name || 'User'}
              </p>
              <p className="text-sm text-muted-foreground truncate">
                {user?.email}
              </p>
            </div>
          </div>

          {/* Settings Options */}
          <div className="space-y-2">
            <Button
              variant="ghost"
              className="w-full justify-start gap-3 h-12"
              onClick={handleNavigateToSettings}
            >
              <UserIcon className="w-5 h-5" />
              <span>Profile Settings</span>
              <ChevronRightIcon className="w-4 h-4 ml-auto" />
            </Button>

            <Button
              variant="ghost"
              className="w-full justify-start gap-3 h-12"
              onClick={() => handleNavigateToSettingsTab('notifications')}
            >
              <BellIcon className="w-5 h-5" />
              <span>Notifications</span>
              <ChevronRightIcon className="w-4 h-4 ml-auto" />
            </Button>

            <Button
              variant="ghost"
              className="w-full justify-start gap-3 h-12"
              onClick={() => handleNavigateToSettingsTab('privacy')}
            >
              <ShieldCheckIcon className="w-5 h-5" />
              <span>Privacy & Security</span>
              <ChevronRightIcon className="w-4 h-4 ml-auto" />
            </Button>

            <Button
              variant="ghost"
              className="w-full justify-start gap-3 h-12"
              onClick={() => handleNavigateToSettingsTab('integrations')}
            >
              <KeyIcon className="w-5 h-5" />
              <span>Integrations</span>
              <ChevronRightIcon className="w-4 h-4 ml-auto" />
            </Button>
          </div>

          {/* Logout Button */}
          <div className="pt-4 border-t border-border">
            <Button
              variant="destructive"
              className="w-full gap-3 h-12"
              onClick={handleLogout}
              disabled={isLoggingOut}
            >
              <ArrowRightOnRectangleIcon className="w-5 h-5" />
              <span>{isLoggingOut ? 'Logging out...' : 'Logout'}</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
