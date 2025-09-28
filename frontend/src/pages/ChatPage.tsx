// frontend/src/pages/ChatPage.tsx
import React from 'react';
import { ChatContainer } from '../components/chat/ChatContainer';

export default function ChatPage() {
  return (
    <div className="h-full flex flex-col bg-background">
      <ChatContainer className="flex-1" />
    </div>
  );
}