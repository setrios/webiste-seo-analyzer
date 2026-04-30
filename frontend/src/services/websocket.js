// WebSocket service with automatic reconnection

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 30000; // 30 seconds
    this.reconnectTimer = null;
    this.token = null;
    this.onMessage = null;
    this.onError = null;
    this.onConnectionChange = null;
  }

  connect(token, onMessage, onError, onConnectionChange) {
    this.token = token;
    this.onMessage = onMessage;
    this.onError = onError;
    this.onConnectionChange = onConnectionChange;

    const wsUrl = `ws://localhost:8000/ws/jobs?token=${token}`;
    
    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.onConnectionChange?.(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message:', data);
          this.onMessage?.(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.onError?.(error);
        this.onConnectionChange?.(false);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.onConnectionChange?.(false);
        this.handleReconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.onError?.(error);
      this.handleReconnect();
    }
  }

  handleReconnect() {
    if (this.reconnectTimer) return;

    // exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (max)
    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    this.reconnectAttempts++;

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect(this.token, this.onMessage, this.onError, this.onConnectionChange);
    }, delay);
  }

  disconnect() {
    console.log('WebSocket disconnecting...');
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// singleton instance
export default new WebSocketService();
