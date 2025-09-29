// frontend/src/services/chat.ts - ENHANCED WITH WEBSOCKET STREAMING
import { useState, useCallback, useRef, useEffect } from 'react';
import { chatApi } from './api';
import { wsService } from './websocket';
import { ChatMessage } from '../types';
import toast from 'react-hot-toast';

interface UseChatStreamReturn {
  sendMessage: (message: string) => Promise<void>;
  stopStream: () => void;
  isStreaming: boolean;
  messages: ChatMessage[];
  isLoading: boolean;
  clearMessages: () => void;
  useWebSocket: boolean;
  toggleWebSocket: (enabled: boolean) => void;
}

export function useChatStream(): UseChatStreamReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [useWebSocket, setUseWebSocket] = useState(true); // Toggle between WebSocket and HTTP
  
  const currentStreamIdRef = useRef<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  /**
   * Clear all messages
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setIsStreaming(false);
    setIsLoading(false);
    currentStreamIdRef.current = null;
  }, []);

  /**
   * Toggle between WebSocket and HTTP mode
   */
  const toggleWebSocket = useCallback((enabled: boolean) => {
    setUseWebSocket(enabled);
    toast(`${enabled ? 'WebSocket' : 'HTTP'} mode enabled`, { icon: 'ℹ️' });
  }, []);

  /**
   * Send message using WebSocket (REAL STREAMING)
   */
  const sendMessageWithWebSocket = useCallback(async (content: string) => {
    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);

    // Create assistant message placeholder for streaming
    const assistantMessageId = `msg-${Date.now()}-assistant`;
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, assistantMessage]);
    setIsStreaming(true);
    setIsLoading(true);
    currentStreamIdRef.current = assistantMessageId;

    // Ensure WebSocket is connected
    if (!wsService.isConnected()) {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        toast.error('Not authenticated. Please log in.');
        setIsStreaming(false);
        setIsLoading(false);
        return;
      }

      wsService.connect(token);
      
      // Wait for connection with timeout
      const connectionTimeout = 5000;
      const startTime = Date.now();
      
      while (!wsService.isConnected() && Date.now() - startTime < connectionTimeout) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      if (!wsService.isConnected()) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: 'Failed to establish WebSocket connection. Switching to HTTP mode...',
                  isStreaming: false,
                }
              : msg
          )
        );
        setIsStreaming(false);
        setIsLoading(false);
        toast.error('WebSocket connection failed');
        
        // Fallback to HTTP
        setUseWebSocket(false);
        return;
      }
    }

    // Send message via WebSocket with streaming callbacks
    wsService.sendChatMessage(
      content,
      
      // onChunk - append content as it arrives
      (chunk: string) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: msg.content + chunk }
              : msg
          )
        );
      },
      
      // onComplete - finalize message
      (metadata?: any) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  isStreaming: false,
                  tool_calls: metadata?.tool_calls,
                }
              : msg
          )
        );
        setIsStreaming(false);
        setIsLoading(false);
        currentStreamIdRef.current = null;
        toast.success('Response complete');
      },
      
      // onError - handle errors
      (error: string) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: msg.content || 'Sorry, an error occurred while streaming the response.',
                  isStreaming: false,
                }
              : msg
          )
        );
        setIsStreaming(false);
        setIsLoading(false);
        currentStreamIdRef.current = null;
        toast.error(`Streaming error: ${error}`);
      }
    );
  }, []);

  /**
   * Send message using HTTP (FALLBACK - NO STREAMING)
   */
  const sendMessageWithHTTP = useCallback(async (content: string) => {
    setIsLoading(true);

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();

    try {
      // Call your existing API
      const response = await chatApi.sendMessage(content);

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
      // Don't show error if request was aborted
      if (error.name === 'AbortError') {
        toast('Request cancelled', { icon: 'ℹ️' });
        return;
      }

      console.error('Failed to send message:', error);
      
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
      abortControllerRef.current = null;
    }
  }, []);

  /**
   * Main sendMessage function - routes to WebSocket or HTTP
   */
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) {
        toast.error('Message cannot be empty');
        return;
      }

      if (useWebSocket) {
        await sendMessageWithWebSocket(content);
      } else {
        await sendMessageWithHTTP(content);
      }
    },
    [useWebSocket, sendMessageWithWebSocket, sendMessageWithHTTP]
  );

  /**
   * Stop streaming
   */
  const stopStream = useCallback(() => {
    if (currentStreamIdRef.current) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === currentStreamIdRef.current
            ? { ...msg, isStreaming: false }
            : msg
        )
      );
      currentStreamIdRef.current = null;
    }

    // Abort HTTP request if exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setIsStreaming(false);
    setIsLoading(false);
    toast('Stream stopped', { icon: '⏹️' });
  }, []);

  return {
    sendMessage,
    stopStream,
    isStreaming,
    messages,
    isLoading,
    clearMessages,
    useWebSocket,
    toggleWebSocket,
  };
}