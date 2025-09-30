// frontend/src/pages/HistoryPage.tsx
import React from 'react';
import { Button } from '../components/ui/Button';
import { ClockIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline';

export default function HistoryPage() {
  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="p-6 border-b border-border">
        <h1 className="text-2xl font-bold text-foreground">Chat History</h1>
        <p className="text-muted-foreground mt-2">View your past conversations</p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          {/* Empty state */}
          <div className="text-center py-12">
            <ClockIcon className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No chat history yet</h3>
            <p className="text-muted-foreground mb-6">
              Start a conversation to see your chat history here.
            </p>
            <Button 
              onClick={() => window.location.href = '/'}
              className="inline-flex items-center gap-2"
            >
              <ChatBubbleLeftIcon className="w-4 h-4" />
              Start New Chat
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
