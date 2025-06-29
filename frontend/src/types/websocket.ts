import type { ProcessingProgress, AudioProcessingResult } from './';

// Type-safe WebSocket communication
export type WebSocketMessageType = 
  | 'processing_progress'
  | 'processing_complete'
  | 'processing_error'
  | 'heartbeat'
  | 'disconnect';

export interface WebSocketMessage<T = unknown> {
  readonly type: WebSocketMessageType;
  readonly payload: T;
  readonly timestamp: string; // ISO 8601
  readonly messageId: string;
}

export interface ProcessingProgressMessage {
  readonly jobId: string;
  readonly progress: ProcessingProgress;
}

export interface ProcessingCompleteMessage {
  readonly jobId: string;
  readonly result: AudioProcessingResult;
  readonly downloadUrl: string;
}

export interface ProcessingErrorMessage {
  readonly jobId: string;
  readonly error: string;
  readonly errorCode: string;
  readonly retryable: boolean;
}

// Type-safe WebSocket hook return type
export interface UseWebSocketReturn {
  readonly isConnected: boolean;
  readonly lastMessage: WebSocketMessage | null;
  readonly connectionError: string | null;
  readonly send: <T>(type: WebSocketMessageType, payload: T) => void;
  readonly disconnect: () => void;
}