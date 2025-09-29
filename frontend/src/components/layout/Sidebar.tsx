// frontend/src/components/layout/Sidebar.tsx
import React from 'react';
import { cn } from '../../lib/utils';
import { useUI, useAppStore } from '../../store/app';
import { Button } from '../ui/Button';
import { 
  ChatBubbleLeftIcon,
  ClockIcon,
  PlusIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';

const sidebarItems = [
  {
    id: 'chat',
    label: 'Chat',
    icon: ChatBubbleLeftIcon,
    active: true,
  },
  {
    id: 'history',
    label: 'History',
    icon: ClockIcon,
    active: false,
  },
];

export function Sidebar() {
  const { sidebarOpen } = useUI();
  const { setSettingsOpen } = useAppStore();

  if (!sidebarOpen) {
    return (
      <div className="w-16 flex flex-col items-center py-4 gap-2">
        <Button variant="ghost" size="icon" className="w-10 h-10">
          <ChatBubbleLeftIcon className="w-5 h-5" />
        </Button>
        <Button variant="ghost" size="icon" className="w-10 h-10">
          <ClockIcon className="w-5 h-5" />
        </Button>
        
        <div className="flex-1" />
        
        <Button 
          variant="ghost" 
          size="icon" 
          className="w-10 h-10"
          onClick={() => setSettingsOpen(true)}
        >
          <Cog6ToothIcon className="w-5 h-5" />
        </Button>
      </div>
    );
  }

  return (
    <div className="w-80 flex flex-col h-full bg-card">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-foreground">Chat</h2>
          <Button variant="ghost" size="icon" className="w-8 h-8">
            <PlusIcon className="w-4 h-4" />
          </Button>
        </div>
        
        <Button variant="outline" className="w-full justify-start" size="sm">
          <PlusIcon className="w-4 h-4 mr-2" />
          New thread
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-2 space-y-1">
          {sidebarItems.map((item) => (
            <Button
              key={item.id}
              variant={item.active ? "secondary" : "ghost"}
              className="w-full justify-start"
              size="sm"
            >
              <item.icon className="w-4 h-4 mr-3" />
              {item.label}
            </Button>
          ))}
        </div>

        <div className="p-4">
          <h3 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider">
            Recent Conversations
          </h3>
          <div className="space-y-2 text-sm text-muted-foreground">
            <div className="text-center py-8">
              <p>No recent conversations</p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-border">
        <Button 
          variant="ghost" 
          className="w-full justify-start" 
          size="sm"
          onClick={() => setSettingsOpen(true)}
        >
          <Cog6ToothIcon className="w-4 h-4 mr-3" />
          Settings
        </Button>
      </div>
    </div>
  );
}
