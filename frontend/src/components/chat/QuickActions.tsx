// frontend/src/components/chat/QuickActions.tsx
import React from 'react';
import { cn } from '../../lib/utils';
import { Avatar } from '../ui/Avatar';

interface QuickAction {
  id: string;
  text: string;
  avatars?: Array<{
    name: string;
    src?: string;
  }>;
}

interface QuickActionsProps {
  onActionClick?: (text: string) => void;
}

const defaultActions: QuickAction[] = [
  {
    id: 'meetings-with',
    text: 'Find meetings I\'ve had with',
    avatars: [
      { name: 'Bill' },
      { name: 'Tim' },
    ],
  },
  {
    id: 'upcoming',
    text: 'Show my upcoming meetings this week',
  },
  {
    id: 'summary',
    text: 'Summarize my meetings from last month',
  },
];

export function QuickActions({ onActionClick }: QuickActionsProps) {
  const handleActionClick = (action: QuickAction) => {
    let messageText = action.text;
    
    if (action.avatars && action.avatars.length > 0) {
      const names = action.avatars.map(a => a.name).join(' and ');
      messageText = `${action.text} ${names} this month`;
    }
    
    if (onActionClick) {
      onActionClick(messageText);
    }
  };

  return (
    <div className="border-t border-border bg-muted/30 py-4">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex flex-wrap gap-2 justify-center">
          {defaultActions.map((action) => (
            <button
              key={action.id}
              onClick={() => handleActionClick(action)}
              className={cn(
                'inline-flex items-center gap-2 px-4 py-2.5',
                'bg-background border border-border rounded-full',
                'text-sm text-foreground',
                'hover:bg-muted hover:border-primary/30 hover:shadow-sm',
                'transition-all duration-200',
                'focus:outline-none focus:ring-2 focus:ring-primary/20'
              )}
            >
              <span>{action.text}</span>
              
              {action.avatars && action.avatars.length > 0 && (
                <div className="flex items-center gap-1">
                  {action.avatars.map((avatar, idx) => (
                    <React.Fragment key={idx}>
                      <Avatar
                        name={avatar.name}
                        src={avatar.src}
                        size="sm"
                        className="ring-1 ring-background"
                      />
                      <span className="font-medium">{avatar.name}</span>
                      {idx < action.avatars!.length - 1 && (
                        <span className="text-muted-foreground">and</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              )}
              
              <span className="text-muted-foreground">this month</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}