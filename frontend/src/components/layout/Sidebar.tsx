// frontend/src/components/layout/Sidebar.tsx - FIXED
import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { useSidebarOpen, useAppStore } from '../../store/app';
import { Button } from '../ui/Button';
import { 
  ChatBubbleLeftIcon,
  ClockIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';

const sidebarItems = [
  {
    id: 'chat',
    label: 'Chat',
    icon: ChatBubbleLeftIcon,
    path: '/',
  },
  {
    id: 'history',
    label: 'History',
    icon: ClockIcon,
    path: '/history',
  },
];

export function Sidebar() {
  // ✅ FIXED: Use individual selector
  const navigate = useNavigate();
  const location = useLocation();
  const sidebarOpen = useSidebarOpen();
  const setSidebarOpen = useAppStore((state) => state.setSidebarOpen);

  // Remove problematic resize logic that was interfering with mobile sidebar

  const handleNewThread = () => {
    console.log('New thread button clicked!');
    
    try {
      // Clear chat and start new conversation
      console.log('Navigating to /');
      navigate('/');
      
      // Clear chat messages by dispatching a custom event
      console.log('Dispatching clearChat event');
      window.dispatchEvent(new CustomEvent('clearChat'));
      
      // Close sidebar on mobile after navigation
      if (window.innerWidth < 768) {
        console.log('Closing sidebar on mobile');
        setSidebarOpen(false);
      }
      
      console.log('New thread process completed');
    } catch (error) {
      console.error('Error in handleNewThread:', error);
    }
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    // Close sidebar on mobile after navigation
    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };

  // Show collapsed sidebar on desktop when sidebarOpen is false
  // On mobile, don't show anything when sidebarOpen is false
  if (!sidebarOpen) {
    return (
      <div className="w-16 flex flex-col items-center py-4 gap-2 hidden md:flex">
        <Button 
          variant="ghost"
          size="icon" 
          className="w-10 h-10"
          onClick={() => handleNavigation('/')}
        >
          <ChatBubbleLeftIcon className="w-5 h-5" />
        </Button>
        <Button 
          variant="ghost" 
          size="icon" 
          className="w-10 h-10"
          onClick={() => handleNavigation('/history')}
        >
          <ClockIcon className="w-5 h-5" />
        </Button>
        
        <div className="flex-1" />
      </div>
    );
  }

  return (
    <div className="w-80 flex flex-col h-full bg-card">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold text-foreground">Chat</h2>
            {/* Mobile close button */}
            <Button
              variant="ghost"
              size="icon"
              className="w-6 h-6 md:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </Button>
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            className="w-8 h-8"
            onClick={handleNewThread}
            title="New thread"
          >
            <PlusIcon className="w-4 h-4" />
          </Button>
        </div>
        
        <Button 
          variant="outline" 
          className="w-full justify-start" 
          size="sm"
          onClick={handleNewThread}
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          New thread
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-2 space-y-1">
          {sidebarItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Button
                key={item.id}
                variant={isActive ? 'secondary' : 'ghost'}
                className={cn(
                  'w-full justify-start',
                  isActive && 'bg-accent'
                )}
                size="sm"
                onClick={() => handleNavigation(item.path)}
              >
                <item.icon className="w-4 h-4 mr-3" />
                {item.label}
              </Button>
            );
          })}
        </div>
      </div>

    </div>
  );
}