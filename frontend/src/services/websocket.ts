/**
 * WebSocket Client Service for Enhanced Matchering Frontend
 * 
 * Handles real-time processing job progress updates from the backend.
 */

/**
 * WebSocket Message Types from Backend
 */
export type WebSocketMessageType = 
  | 'connection_established'
  | 'processing_progress'
  | 'job_completed'
  | 'job_failed'
  | 'error';

/**
 * WebSocket Message Structure
 */
export interface WebSocketMessage {
  type: WebSocketMessageType;
  payload: Record<string, any>;
  timestamp: string;
  message_id: string;
}

/**
 * Connection Established Payload
 */
export interface ConnectionEstablishedPayload {
  job_id: string;
  message: string;
}

/**
 * Processing Progress Payload
 */
export interface ProcessingProgressPayload {
  job_id: string;
  status: string;
  progress_percentage: number;
  current_stage: string;
  message: string;
  elapsed_time: number;
  remaining_time: number;
}

/**
 * AI Predictions from processing
 */
export interface AIPredictions {
  modelUsed: string;
  confidence: number;
  predictedGenre: string;
  isUsingFallbackGenre?: boolean;
  audioCharacteristics: Record<string, any>;
  processingTime: number;
}

/**
 * Job Completed Payload
 */
export interface JobCompletedPayload {
  job_id: string;
  status: string;
  message: string;
  output_file_url?: string;
  ai_predictions?: AIPredictions;
  processing_metadata?: Record<string, any>;
}

/**
 * Job Failed Payload
 */
export interface JobFailedPayload {
  job_id: string;
  status: string;
  error: string;
  error_code: string;
}

/**
 * Error Payload
 */
export interface ErrorPayload {
  job_id: string;
  error: string;
  error_code: string;
}

/**
 * WebSocket Event Handlers
 */
export interface WebSocketEventHandlers {
  onConnectionEstablished?: (payload: ConnectionEstablishedPayload) => void;
  onProcessingProgress?: (payload: ProcessingProgressPayload) => void;
  onJobCompleted?: (payload: JobCompletedPayload) => void;
  onJobFailed?: (payload: JobFailedPayload) => void;
  onError?: (payload: ErrorPayload) => void;
  onConnectionError?: (error: Event) => void;
  onConnectionClosed?: (event: CloseEvent) => void;
}

/**
 * WebSocket Client Configuration
 */
export interface WebSocketConfig {
  baseUrl?: string;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
}

/**
 * WebSocket Connection State
 */
export type WebSocketState = 'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting';

/**
 * Enhanced WebSocket Client for Job Progress Updates
 */
export class JobProgressWebSocket {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private handlers: WebSocketEventHandlers = {};
  private state: WebSocketState = 'disconnected';
  private reconnectCount = 0;
  private heartbeatTimer: number | null = null;
  private reconnectTimer: number | null = null;
  private jobId: string | null = null;

  constructor(config: WebSocketConfig = {}) {
    this.config = {
      baseUrl: config.baseUrl || 'ws://localhost:8000',
      reconnectAttempts: config.reconnectAttempts || 5,
      reconnectInterval: config.reconnectInterval || 3000,
      heartbeatInterval: config.heartbeatInterval || 30000,
    };
  }

  /**
   * Connect to WebSocket for a specific job
   */
  connect(jobId: string, handlers: WebSocketEventHandlers = {}): Promise<void> {
    return new Promise((resolve, reject) => {
      this.jobId = jobId;
      this.handlers = handlers;
      this.state = 'connecting';

      // Clean up existing connection
      this.disconnect();

      const wsUrl = `${this.config.baseUrl}/api/v1/processing/ws/${jobId}`;
      console.log(`[WebSocket] Connecting to: ${wsUrl}`);

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = (event) => {
          console.log(`[WebSocket] Connected to job: ${jobId}`);
          this.state = 'connected';
          this.reconnectCount = 0;
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onerror = (error) => {
          console.error(`[WebSocket] Connection error:`, error);
          this.state = 'error';
          this.handlers.onConnectionError?.(error);
          reject(new Error('WebSocket connection failed'));
        };

        this.ws.onclose = (event) => {
          console.log(`[WebSocket] Connection closed:`, event);
          this.state = 'disconnected';
          this.stopHeartbeat();
          this.handlers.onConnectionClosed?.(event);

          // Attempt reconnection if not manually closed
          if (event.code !== 1000 && this.shouldReconnect()) {
            this.scheduleReconnect();
          }
        };

      } catch (error) {
        console.error(`[WebSocket] Failed to create connection:`, error);
        this.state = 'error';
        reject(error);
      }
    });
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      console.log(`[WebSocket] Disconnecting from job: ${this.jobId}`);
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    this.stopHeartbeat();
    this.stopReconnectTimer();
    this.state = 'disconnected';
    this.jobId = null;
  }

  /**
   * Get current connection state
   */
  getState(): WebSocketState {
    return this.state;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.state === 'connected' && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      console.log(`[WebSocket] Received message:`, message);

      switch (message.type) {
        case 'connection_established':
          this.handlers.onConnectionEstablished?.(message.payload as ConnectionEstablishedPayload);
          break;

        case 'processing_progress':
          this.handlers.onProcessingProgress?.(message.payload as ProcessingProgressPayload);
          break;

        case 'job_completed':
          this.handlers.onJobCompleted?.(message.payload as JobCompletedPayload);
          break;

        case 'job_failed':
          this.handlers.onJobFailed?.(message.payload as JobFailedPayload);
          break;

        case 'error':
          this.handlers.onError?.(message.payload as ErrorPayload);
          break;

        default:
          console.warn(`[WebSocket] Unknown message type: ${message.type}`);
      }

    } catch (error) {
      console.error(`[WebSocket] Failed to parse message:`, error);
    }
  }

  /**
   * Check if should attempt reconnection
   */
  private shouldReconnect(): boolean {
    return this.reconnectCount < this.config.reconnectAttempts && this.jobId !== null;
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (!this.shouldReconnect()) {
      console.log(`[WebSocket] Max reconnection attempts reached`);
      return;
    }

    this.state = 'reconnecting';
    this.reconnectCount++;
    
    const delay = this.config.reconnectInterval * Math.pow(1.5, this.reconnectCount - 1);
    console.log(`[WebSocket] Scheduling reconnect attempt ${this.reconnectCount} in ${delay}ms`);

    this.reconnectTimer = window.setTimeout(() => {
      if (this.jobId) {
        console.log(`[WebSocket] Attempting reconnect ${this.reconnectCount}/${this.config.reconnectAttempts}`);
        this.connect(this.jobId, this.handlers).catch((error) => {
          console.error(`[WebSocket] Reconnect attempt ${this.reconnectCount} failed:`, error);
        });
      }
    }, delay);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = window.setInterval(() => {
      if (this.isConnected()) {
        // Send ping if WebSocket supports it, otherwise just check connection
        try {
          this.ws?.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }));
        } catch (error) {
          console.warn(`[WebSocket] Heartbeat failed:`, error);
        }
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Stop heartbeat timer
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Stop reconnect timer
   */
  private stopReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}

/**
 * Singleton WebSocket manager for the application
 */
class WebSocketManager {
  private connections: Map<string, JobProgressWebSocket> = new Map();

  /**
   * Get or create WebSocket connection for a job
   */
  getConnection(jobId: string, config?: WebSocketConfig): JobProgressWebSocket {
    if (!this.connections.has(jobId)) {
      this.connections.set(jobId, new JobProgressWebSocket(config));
    }
    return this.connections.get(jobId)!;
  }

  /**
   * Disconnect and remove connection for a job
   */
  disconnectJob(jobId: string): void {
    const connection = this.connections.get(jobId);
    if (connection) {
      connection.disconnect();
      this.connections.delete(jobId);
    }
  }

  /**
   * Disconnect all connections
   */
  disconnectAll(): void {
    for (const [jobId, connection] of this.connections) {
      connection.disconnect();
    }
    this.connections.clear();
  }

  /**
   * Get connection states for all jobs
   */
  getConnectionStates(): Record<string, WebSocketState> {
    const states: Record<string, WebSocketState> = {};
    for (const [jobId, connection] of this.connections) {
      states[jobId] = connection.getState();
    }
    return states;
  }
}

// Export singleton instance
export const webSocketManager = new WebSocketManager();