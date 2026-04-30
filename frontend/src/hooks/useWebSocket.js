import { useEffect, useState, useCallback } from 'react';
import websocketService from '../services/websocket';

export const useWebSocket = (onMessage) => {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);

  // memoize callback to prevent reconnections on every render
  const handleMessage = useCallback((data) => {
    onMessage(data);
  }, [onMessage]);

  const handleError = useCallback((err) => {
    setError(err);
  }, []);

  const handleConnectionChange = useCallback((isConnected) => {
    setConnected(isConnected);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('No token found for WebSocket connection');
      return;
    }

    console.log('Initializing WebSocket connection...');
    websocketService.connect(token, handleMessage, handleError, handleConnectionChange);

    // check connection status periodically
    const statusInterval = setInterval(() => {
      const isConnected = websocketService.isConnected();
      setConnected(isConnected);
    }, 1000);

    return () => {
      console.log('Cleaning up WebSocket connection...');
      clearInterval(statusInterval);
      websocketService.disconnect();
    };
  }, [handleMessage, handleError, handleConnectionChange]);

  return { connected, error };
};
