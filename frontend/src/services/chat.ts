// frontend/src/services/chat.ts - ENHANCED WITH WEBSOCKET STREAMING
import { useState, useCallback, useRef, useEffect } from 'react';
import { chatApi, api } from './api';
import { wsService } from './websocket';
import { ChatMessage } from '../types';
import { useAuthStore } from '../store/auth';
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
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [useWebSocket, setUseWebSocket] = useState(true);
  const currentStreamIdRef = useRef<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Clear all messages
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    currentStreamIdRef.current = null;
    setIsStreaming(false);
    setIsLoading(false);
  }, []);

  /**
   * Toggle between WebSocket and HTTP mode
   */
  const toggleWebSocket = useCallback((enabled: boolean) => {
    setUseWebSocket(enabled);
    toast(`${enabled ? 'WebSocket' : 'HTTP'} mode enabled`, { icon: 'ℹ️' });
  }, []);

  /**
   * Send message using HTTP (Server-Sent Events)
   */
  const sendMessageWithHTTP = useCallback(async (content: string) => {
    setIsLoading(true);
    setIsStreaming(true);

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
    currentStreamIdRef.current = assistantMessageId;

    try {
      // Use the streaming API endpoint
      const response = await api.stream('/chat/stream', { message: content });
      const reader = response.getReader();
      const decoder = new TextDecoder();

      let buffer = '';
      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const eventData = JSON.parse(line.slice(6));
              switch (eventData.type) {
                case 'content':
                  const chunk = eventData.content || '';
                  accumulatedContent += chunk;
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, content: msg.content + chunk }
                        : msg
                    )
                  );
                  break;
                case 'tool_use_start':
                  console.log('Tool use started:', eventData.tool_name);
                  break;
                case 'tool_result':
                  console.log('Tool result:', eventData.result);
                  break;
                case 'done':
                  console.log('Stream completed');
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, isStreaming: false }
                        : msg
                    )
                  );
                  setIsStreaming(false);
                  setIsLoading(false);
                  currentStreamIdRef.current = null;
                  return;
                case 'error':
                  console.error('Stream error:', eventData.error);
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? {
                            ...msg,
                            content: msg.content || 'Sorry, an error occurred while processing your request.',
                            isStreaming: false,
                          }
                        : msg
                    )
                  );
                  setIsStreaming(false);
                  setIsLoading(false);
                  currentStreamIdRef.current = null;
                  toast.error(`Error: ${eventData.error}`);
                  return;
              }
            } catch (parseError) {
              console.error('Failed to parse SSE event:', parseError);
            }
          }
        }
      }

      // Finalize message if stream ended without 'done' event
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, isStreaming: false }
            : msg
        )
      );
      setIsStreaming(false);
      setIsLoading(false);
      currentStreamIdRef.current = null;

    } catch (error: any) {
      console.error('Failed to send message:', error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: msg.content || 'Sorry, I encountered an error. Please try again.',
                isStreaming: false,
              }
            : msg
        )
      );
      setIsStreaming(false);
      setIsLoading(false);
      currentStreamIdRef.current = null;
      toast.error('Failed to send message');
    }
  }, []);

  /**
   * Send message using WebSocket (REAL STREAMING)
   */
  const sendMessageWithWebSocket = useCallback(async (content: string) => {
    // Check if WebSocket is connected
    if (!wsService.isConnected()) {
      console.log('⚠️ WebSocket not connected, falling back to HTTP');
      await sendMessageWithHTTP(content);
      return;
    }

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
      const token = useAuthStore.getState().token;
      
      if (!token) {
        toast.error('Not authenticated. Please log in.');
        setIsStreaming(false);
        setIsLoading(false);
        return;
      }

      // Try to connect WebSocket
      wsService.connect(token);
      
      // Wait a bit for connection
      for (let i = 0; i < 10; i++) {
        if (wsService.isConnected()) break;
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
  }, [sendMessageWithHTTP]);

  /**
   * Main sendMessage function - routes to WebSocket or HTTP
   */
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) {
        toast.error('Message cannot be empty');
        return;
      }

      console.log('🚀 Sending message:', { 
        content, 
        useWebSocket, 
        wsConnected: wsService.isConnected(),
        wsStatus: wsService.getStatus()
      });

      try {
        if (useWebSocket) {
          console.log('📡 Using WebSocket for message');
          await sendMessageWithWebSocket(content);
        } else {
          console.log('🌐 Using HTTP for message');
          await sendMessageWithHTTP(content);
        }
      } catch (error) {
        console.error('❌ Error in sendMessage:', error);
        toast.error('Failed to send message. Please try again.');
      }
    },
    [useWebSocket]
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