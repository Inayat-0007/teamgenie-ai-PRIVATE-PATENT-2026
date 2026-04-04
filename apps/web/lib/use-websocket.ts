'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

// --- Local types (avoids @teamgenie/shared dependency resolution) ---
interface WSMessage<T = unknown> {
  readonly type: 'score_update' | 'player_update' | 'match_status' | 'heartbeat';
  readonly payload: T;
  readonly timestamp: number;
}

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace('http', 'ws');

const API_TIMEOUT_MS = 30_000;
const API_RETRY_COUNT = 3;

interface UseWebSocketOptions {
  matchId: string;
  onMessage?: (msg: WSMessage) => void;
  reconnectInterval?: number;
  maxReconnects?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WSMessage | null;
  reconnectCount: number;
  send: (data: string) => void;
  disconnect: () => void;
}

/**
 * Custom hook for real-time match updates via WebSocket.
 * Auto-reconnects with exponential backoff.
 */
export function useWebSocket({
  matchId,
  onMessage,
  reconnectInterval = 3000,
  maxReconnects = 10,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const [reconnectCount, setReconnectCount] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);

  const cleanup = useCallback(() => {
    if (heartbeatRef.current) clearInterval(heartbeatRef.current);
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    cleanup();

    const url = `${WS_BASE_URL}/api/match/${matchId}/ws`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setReconnectCount(0);

      // Heartbeat every 30s
      heartbeatRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30_000);
    };

    ws.onmessage = (event) => {
      if (event.data === 'pong') return; // heartbeat response

      try {
        const msg: WSMessage = JSON.parse(event.data);
        setLastMessage(msg);
        onMessage?.(msg);
      } catch {
        // Non-JSON message — ignore
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);

      // Auto-reconnect with exponential backoff
      setReconnectCount((prev) => {
        if (prev < maxReconnects) {
          const delay = reconnectInterval * Math.pow(1.5, prev);
          reconnectTimerRef.current = setTimeout(connect, delay);
          return prev + 1;
        }
        return prev;
      });
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [matchId, onMessage, reconnectInterval, maxReconnects, cleanup]);

  useEffect(() => {
    connect();
    return cleanup;
  }, [connect, cleanup]);

  const send = useCallback((data: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  const disconnect = useCallback(() => {
    setReconnectCount(Infinity); // prevent auto-reconnect
    cleanup();
    setIsConnected(false);
  }, [cleanup]);

  return { isConnected, lastMessage, reconnectCount, send, disconnect };
}

export type { WSMessage, UseWebSocketOptions, UseWebSocketReturn };
export default useWebSocket;
