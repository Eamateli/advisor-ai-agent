// frontend/src/services/chat.ts
import { useState, useCallback } from 'react';
import { chatApi } from './api';
import { ChatMessage } from '../types';
import toast from 'react-hot-toast';

interface UseChatStreamReturn {
  sendMessage: (message: string) => Promise<void>;
  stopStream: () => void;
  isStreaming: boolean;
  messages: ChatMessage[];
  isLoading: boolean;
}

export function useChatStream(): UseChatStreamReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const sendMessage = useCallback(async (content: string) => {
    setIsLoading(true);

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      // Call your existing API - it takes just message string
      const response = await chatApi.sendMessage(content);

      // Backend returns streaming data, but for now we'll handle the final response
      // The response structure from your backend might be different
      // Adjust based on what your /chat/stream endpoint actually returns
      
      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: response.response || response.content || 'No response',
        created_at: new Date().toISOString(),
        tool_calls: response.tool_calls,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      toast.success('Message sent');
    } catch (error: any) {
      console.error('Failed to send message:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: error?.response?.data?.error || 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),
      };
      
      setMessages((prev) => [...prev, errorMessage]);
      toast.error('Failed to send message');
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  }, []);

  const stopStream = useCallback(() => {
    setIsStreaming(false);
    // TODO: Implement WebSocket stream cancellation when ready
  }, []);

  return {
    sendMessage,
    stopStream,
    isStreaming,
    messages,
    isLoading,
  };
}