/* Pixel Office — Resilient Typed WebSocket Client */

import { ConnectionStatus, OfficeWebSocketEvent } from '../types/office';

export type EventCallback = (event: OfficeWebSocketEvent) => void;
export type StatusCallback = (status: ConnectionStatus) => void;

export class OfficeWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private status: ConnectionStatus = 'DISCONNECTED';
  private eventListeners: Set<EventCallback> = new Set();
  private statusListeners: Set<StatusCallback> = new Set();
  private processedEventIds: Set<string> = new Set();
  
  private pingInterval: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private isManuallyClosed = false;

  constructor(url: string = `ws://${window.location.host}/ws/office`) {
    // Standardize URL protocol
    const loc = window.location;
    const protocol = loc.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = url || `${protocol}//${loc.host}/office/ws`;
  }

  connect(): void {
    this.isManuallyClosed = false;
    this.updateStatus(this.reconnectAttempts > 0 ? 'RECONNECTING' : 'DISCONNECTED');

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.updateStatus('CONNECTED');
        this.startPingHeartbeat();
      };

      this.ws.onmessage = (messageEvent) => {
        try {
          const raw = messageEvent.data;
          if (raw === 'pong') return;

          const parsed: OfficeWebSocketEvent = JSON.parse(raw);
          if (parsed.event_id) {
            if (this.processedEventIds.has(parsed.event_id)) return;
            this.processedEventIds.add(parsed.event_id);
            if (this.processedEventIds.size > 500) {
              const first = Array.from(this.processedEventIds)[0];
              this.processedEventIds.delete(first);
            }
          }

          this.eventListeners.forEach((cb) => cb(parsed));
        } catch (err) {
          // Log parsing error silently
        }
      };

      this.ws.onerror = () => {
        this.updateStatus('STALE');
      };

      this.ws.onclose = () => {
        this.stopPingHeartbeat();
        if (!this.isManuallyClosed) {
          this.updateStatus('DISCONNECTED');
          this.scheduleReconnect();
        }
      };
    } catch (err) {
      this.updateStatus('DISCONNECTED');
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    this.isManuallyClosed = true;
    this.stopPingHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.updateStatus('DISCONNECTED');
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.updateStatus('STALE');
      return;
    }

    const backoffMs = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 15000);
    this.reconnectAttempts++;
    this.updateStatus('RECONNECTING');

    setTimeout(() => {
      if (!this.isManuallyClosed && this.status !== 'CONNECTED') {
        this.connect();
      }
    }, backoffMs);
  }

  private startPingHeartbeat(): void {
    this.stopPingHeartbeat();
    this.pingInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 15000);
  }

  private stopPingHeartbeat(): void {
    if (this.pingInterval !== null) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  onEvent(callback: EventCallback): () => void {
    this.eventListeners.add(callback);
    return () => this.eventListeners.delete(callback);
  }

  onStatusChange(callback: StatusCallback): () => void {
    this.statusListeners.add(callback);
    callback(this.status);
    return () => this.statusListeners.delete(callback);
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  private updateStatus(newStatus: ConnectionStatus): void {
    this.status = newStatus;
    this.statusListeners.forEach((cb) => cb(newStatus));
  }
}

export const wsClient = new OfficeWebSocketClient();
