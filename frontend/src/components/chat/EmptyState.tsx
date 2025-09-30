// frontend/src/components/chat/EmptyState.tsx
import React from 'react';
import { cn } from '../../lib/utils';
import { 
  ChatBubbleLeftRightIcon,
  SparklesIcon 
} from '@heroicons/react/24/outline';

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] px-4">
      <div className="relative mb-6">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <ChatBubbleLeftRightIcon className="w-8 h-8 text-white" />
        </div>
        <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-yellow-400 flex items-center justify-center">
          <SparklesIcon className="w-4 h-4 text-yellow-900" />
        </div>
      </div>

      <h2 className="text-2xl font-semibold text-foreground mb-2 text-center">
        Start a conversation
      </h2>
      
      <p className="text-muted-foreground text-center max-w-md mb-8">
        Type a message below to get started
      </p>

    </div>
  );
}
