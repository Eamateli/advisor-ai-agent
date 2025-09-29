class WebSocketService {
  private ws: WebSocket | null = null;
  
  connect() {
    console.log('WebSocket connect - stub implementation');
  }
  
  disconnect() {
    console.log('WebSocket disconnect - stub implementation');
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const wsService = new WebSocketService();
