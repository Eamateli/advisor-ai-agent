// frontend/src/components/chat/ChatContainer.tsx
import React, { useEffect, useRef, useState } from 'react';
import { cn } from '../../lib/utils';
import { useChatStore } from '../../store/chat';
import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';
import { ContextHeader } from './ContextHeader';
import { QuickActions } from './QuickActions';
import { EmptyState } from './EmptyState';
import { ScrollArea } from '../ui/ScrollArea';

interface ChatContainerProps {
  className?: string;
}

export function ChatContainer({ className }: ChatContainerProps) {
  const { messages, isLoading, currentThreadId } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  const hasMessages = messages.length > 0;

  return (
    <div className={cn('flex flex-col h-full bg-background', className)}>
      {/* Context Header - Shows current context (e.g., "All meetings") */}
      <ContextHeader />

      {/* Main chat area */}
      <div className="flex-1 overflow-hidden relative">
        <ScrollArea className="h-full">
          <div className="max-w-4xl mx-auto px-4 py-6">
            {hasMessages ? (
              <>
                {/* Message List */}
                <MessageList messages={messages} />
                
                {/* Scroll anchor */}
                <div ref={messagesEndRef} />
              </>
            ) : (
              /* Empty state when no messages */
              <EmptyState />
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Quick Actions - Suggestion pills */}
      {!hasMessages && <QuickActions />}

      {/* Chat Input */}
      <div className="border-t border-border bg-background">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <ChatInput />
        </div>
      </div>
    </div>
  );
}