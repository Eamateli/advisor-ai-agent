// frontend/src/components/chat/ChatContainer.tsx
import React, { useEffect, useRef } from 'react';
import { cn, scrollToBottom } from '../../lib/utils';
import { useChatStream } from '../../services/chat';
import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';
import { ContextHeader } from './ContextHeader';
import { QuickActions } from './QuickActions';
import { EmptyState } from './EmptyState';

interface ChatContainerProps {
  className?: string;
}

export function ChatContainer({ className }: ChatContainerProps) {
  const { messages, isLoading, sendMessage, clearMessages } = useChatStream();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (containerRef.current) {
      scrollToBottom(containerRef.current);
    }
  }, [messages]);

  // Listen for clear chat event from sidebar
  useEffect(() => {
    const handleClearChat = () => {
      console.log('ChatContainer: Received clearChat event, clearing messages');
      clearMessages();
    };

    window.addEventListener('clearChat', handleClearChat);
    return () => window.removeEventListener('clearChat', handleClearChat);
  }, [clearMessages]);

  const hasMessages = messages.length > 0;

  return (
    <div className={cn('flex flex-col h-full bg-background', className)}>
      {/* Context Header - only show when there are messages */}
      {hasMessages && (
        <ContextHeader
          contextLabel="current conversation"
        />
      )}

      {/* Main chat area */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-y-auto"
      >
        <div className="max-w-4xl mx-auto px-4 py-6">
          {hasMessages ? (
            <>
              <MessageList messages={messages} />
              <div ref={messagesEndRef} />
            </>
          ) : (
            <EmptyState />
          )}
        </div>
      </div>

      {/* Quick Actions - only show when no messages */}
      {!hasMessages && <QuickActions onActionClick={sendMessage} />}

      {/* Chat Input */}
      <div className="border-t border-border bg-background">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <ChatInput 
            onSendMessage={sendMessage}
            disabled={isLoading}
          />
        </div>
      </div>
    </div>
  );
}