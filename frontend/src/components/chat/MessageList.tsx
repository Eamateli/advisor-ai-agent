// frontend/src/components/chat/MessageList.tsx
import React from 'react';
import { cn } from '../../lib/utils';
import { MessageBubble } from './MessageBubble';
import { MeetingCard } from './MeetingCard';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  isStreaming?: boolean;
  metadata?: {
    meetings?: any[];
    [key: string]: any;
  };
}

interface MessageListProps {
  messages: Message[];
  className?: string;
}

export function MessageList({ messages, className }: MessageListProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {messages.map((message, index) => {
        const isLatest = index === messages.length - 1;
        
        return (
          <div key={message.id}>
            <MessageBubble 
              message={message} 
              isLatest={isLatest}
            />
            
            {message.metadata?.meetings && (
              <div className="mt-4 space-y-3">
                {message.metadata.meetings.map((meeting: any) => (
                  <MeetingCard 
                    key={meeting.id} 
                    meeting={meeting}
                  />
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}