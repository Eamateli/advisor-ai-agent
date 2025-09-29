// frontend/src/components/chat/MessageList.tsx
import React from 'react';
import { cn } from '../../lib/utils';
import { MessageBubble } from './MessageBubble';
import { MeetingCard } from './MeetingCard';
import { ChatMessage, Meeting } from '../../types';

interface MessageListProps {
  messages: ChatMessage[];
  className?: string;
}

export function MessageList({ messages, className }: MessageListProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {messages.map((message, index) => {
        const isLatest = index === messages.length - 1;
        
        // Extract meetings from tool_calls if they exist
        const meetings: Meeting[] = [];
        
        if (message.tool_calls) {
          message.tool_calls.forEach(toolCall => {
            if (toolCall.function.name === 'search_calendar_events' && toolCall.result?.meetings) {
              meetings.push(...toolCall.result.meetings);
            }
          });
        }
        
        return (
          <div key={message.id}>
            <MessageBubble 
              message={message} 
              isLatest={isLatest}
            />
            
            {meetings.length > 0 && (
              <div className="mt-4 space-y-3">
                {meetings.map((meeting) => (
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