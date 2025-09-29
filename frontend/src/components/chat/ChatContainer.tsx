import React from 'react';

interface ChatContainerProps {
  className?: string;
}

export function ChatContainer({ className }: ChatContainerProps) {
  return (
    <div className={`flex items-center justify-center h-full ${className || ''}`}>
      <p className="text-muted-foreground">Chat interface - coming soon</p>
    </div>
  );
}
