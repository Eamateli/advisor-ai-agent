// frontend/src/services/websocket.ts - COMPLETE IMPLEMENTATION
import { config, wsConfig } from '../lib/config';
import { useAuthStore } from '../store/auth';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnecting' | 'disconnected' | 'error';

export interface WebSocketMessage {
  type: 'chat' | 'status' | 'error' | 'ping' | 'pong' | 'stream_start' | 'stream_chunk' | 'stream_end';
  data?: any;
  timestamp: string;
  messageId?: string;
}

export interface StreamChunk {
  content: string;
  isComplete: boolean;
  metadata?: {
    sources?: any[];
    meetings?: any[];
    [key: string]: any;
  };
}

type MessageCallback = (message: WebSocketMessage) => void;
type StatusCallback = (status: WebSocketStatus) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private status: WebSocketStatus = 'disconnected';
  private messageCallbacks: Set<MessageCallback> = new Set();
  private statusCallbacks: Set<StatusCallback> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private pingInterval: NodeJS.Timeout | null = null;
  private accessToken: string | null = null;

  /**
   * Initialize WebSocket connection
   */
  connect(token?: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('✅ WebSocket already connected');
      return;
    }

    // Disconnect existing connection if any
    if (this.ws) {
      this.disconnect();
    }

    if (token) {
      this.accessToken = token;
    } else {
      // Get token from auth store if not provided
      const authStore = useAuthStore.getState();
      if (authStore.token && authStore.isTokenValid()) {
        this.accessToken = authStore.token;
      } else {
        console.error('❌ No valid token available for WebSocket connection');
        this.setStatus('error');
        return;
      }
    }

    console.log('🔄 Connecting WebSocket with token:', this.accessToken ? 'present' : 'missing');

    this.setStatus('connecting');

    try {
      // Build WebSocket URL with authentication
      const wsUrl = new URL(config.WS_URL);
      if (this.accessToken) {
        wsUrl.searchParams.set('token', this.accessToken);
      }

      this.ws = new WebSocket(wsUrl.toString());

      // Connection opened
      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.setStatus('connected');
        this.reconnectAttempts = 0;
        this.startPingInterval();
      };

      // Handle incoming messages
      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      // Connection closed
      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        this.setStatus('disconnected');
        this.stopPingInterval();

        // Attempt to reconnect if not intentional closure
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          
          setTimeout(() => {
            this.connect();
          }, delay);
        }
      };

      // Connection error
      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.setStatus('error');
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.setStatus('error');
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (!this.ws) return;

    this.setStatus('disconnecting');
    this.stopPingInterval();
    
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.close(1000, 'Client disconnect');
    }
    
    this.ws = null;
    this.setStatus('disconnected');
  }

  /**
   * Send a message through WebSocket
   */
  send(message: Partial<WebSocketMessage>): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      throw new Error('WebSocket is not connected');
    }

    const fullMessage: WebSocketMessage = {
      type: message.type || 'chat',
      data: message.data,
      timestamp: new Date().toISOString(),
      messageId: message.messageId,
    };

    this.ws.send(JSON.stringify(fullMessage));
  }

  /**
   * Send a chat message and handle streaming response
   */
  async sendChatMessage(
    content: string,
    onChunk: (chunk: string) => void,
    onComplete: (metadata?: any) => void,
    onError: (error: string) => void
  ): Promise<void> {
    if (!this.isConnected()) {
      console.log('⚠️ WebSocket not connected, cannot send chat message');
      onError('WebSocket not connected');
      return;
    }

    const messageId = `msg-${Date.now()}`;
    let accumulatedContent = '';

    // Set up temporary listener for this specific message
    const handleStreamChunk = (message: WebSocketMessage) => {
      if (message.messageId !== messageId) return;

      console.log('📨 WebSocket message received:', message.type, message.data);

      switch (message.type) {
        case 'stream_start':
          console.log('📡 Stream started');
          break;

        case 'stream_chunk':
          // Handle different event types from the agent
          if (message.data?.type === 'content') {
            const chunk = message.data?.content || '';
            accumulatedContent += chunk;
            console.log('📝 Content chunk:', chunk);
            onChunk(chunk);
          }
          break;

        case 'stream_end':
          console.log('✅ Stream completed');
          onComplete(message.data?.metadata);
          this.removeMessageCallback(handleStreamChunk);
          break;

        case 'error':
          console.error('❌ Stream error:', message.data);
          onError(message.data?.message || 'Unknown error');
          this.removeMessageCallback(handleStreamChunk);
          break;
      }
    };

    // Add the listener
    this.addMessageCallback(handleStreamChunk);

    // Send the message
    try {
      console.log('📤 Sending WebSocket message:', { type: 'chat', content, messageId });
      this.send({
        type: 'chat',
        data: { content },
        messageId,
      });
    } catch (error) {
      console.error('❌ Failed to send WebSocket message:', error);
      this.removeMessageCallback(handleStreamChunk);
      onError(error instanceof Error ? error.message : 'Failed to send message');
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get current connection status
   */
  getStatus(): WebSocketStatus {
    return this.status;
  }

  /**
   * Add a message callback
   */
  addMessageCallback(callback: MessageCallback): void {
    this.messageCallbacks.add(callback);
  }

  /**
   * Remove a message callback
   */
  removeMessageCallback(callback: MessageCallback): void {
    this.messageCallbacks.delete(callback);
  }

  /**
   * Add a status callback
   */
  addStatusCallback(callback: StatusCallback): void {
    this.statusCallbacks.add(callback);
  }

  /**
   * Remove a status callback
   */
  removeStatusCallback(callback: StatusCallback): void {
    this.statusCallbacks.delete(callback);
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(message: WebSocketMessage): void {
    // Handle ping/pong
    if (message.type === 'ping') {
      this.send({ type: 'pong', timestamp: new Date().toISOString() });
      return;
    }

    // Notify all callbacks
    this.messageCallbacks.forEach(callback => {
      try {
        callback(message);
      } catch (error) {
        console.error('Error in message callback:', error);
      }
    });
  }

  /**
   * Update connection status
   */
  private setStatus(status: WebSocketStatus): void {
    this.status = status;
    this.statusCallbacks.forEach(callback => {
      try {
        callback(status);
      } catch (error) {
        console.error('Error in status callback:', error);
      }
    });
  }

  /**
   * Start ping interval to keep connection alive
   */
  private startPingInterval(): void {
    this.stopPingInterval();
    this.pingInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping', timestamp: new Date().toISOString() });
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Stop ping interval
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
}

// Export singleton instance
export const wsService = new WebSocketService();