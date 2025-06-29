/**
 * React Hook for Job Progress WebSocket Updates
 * 
 * Provides real-time progress updates for processing jobs using WebSocket connection.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  webSocketManager, 
  JobProgressWebSocket,
  WebSocketState,
  ProcessingProgressPayload,
  JobCompletedPayload,
  JobFailedPayload,
  ConnectionEstablishedPayload,
  ErrorPayload
} from '@/services/websocket';

/**
 * Job Progress State
 */
export interface JobProgressState {
  jobId: string | null;
  connectionState: WebSocketState;
  isConnected: boolean;
  progress: number;
  currentStage: string;
  status: string;
  message: string;
  elapsedTime: number;
  remainingTime: number;
  isCompleted: boolean;
  isFailed: boolean;
  error: string | null;
  outputFileUrl: string | null;
}

/**
 * Job Progress Hook Options
 */
export interface UseJobProgressOptions {
  autoConnect?: boolean;
  onProgressUpdate?: (progress: ProcessingProgressPayload) => void;
  onJobCompleted?: (completion: JobCompletedPayload) => void;
  onJobFailed?: (failure: JobFailedPayload) => void;
  onConnectionError?: (error: string) => void;
  wsConfig?: {
    baseUrl?: string;
    reconnectAttempts?: number;
    reconnectInterval?: number;
  };
}

/**
 * Job Progress Hook Return Type
 */
export interface UseJobProgressReturn {
  // Connection management
  connect: (jobId: string) => Promise<void>;
  disconnect: () => void;
  reconnect: () => Promise<void>;
  
  // State
  state: JobProgressState;
  
  // Utilities
  formatProgress: () => string;
  formatTimeRemaining: () => string;
  formatElapsedTime: () => string;
}

/**
 * Initial state for job progress
 */
const initialState: JobProgressState = {
  jobId: null,
  connectionState: 'disconnected',
  isConnected: false,
  progress: 0,
  currentStage: '',
  status: 'pending',
  message: '',
  elapsedTime: 0,
  remainingTime: 0,
  isCompleted: false,
  isFailed: false,
  error: null,
  outputFileUrl: null,
};

/**
 * Hook for managing WebSocket job progress updates
 */
export const useJobProgress = (options: UseJobProgressOptions = {}): UseJobProgressReturn => {
  const [state, setState] = useState<JobProgressState>(initialState);
  const connectionRef = useRef<JobProgressWebSocket | null>(null);
  const optionsRef = useRef(options);

  // Update options ref when options change
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  /**
   * Update connection state
   */
  const updateConnectionState = useCallback((connectionState: WebSocketState) => {
    setState(prev => ({
      ...prev,
      connectionState,
      isConnected: connectionState === 'connected',
    }));
  }, []);

  /**
   * Handle connection established
   */
  const handleConnectionEstablished = useCallback((payload: ConnectionEstablishedPayload) => {
    console.log(`[JobProgress] Connection established for job: ${payload.job_id}`);
    setState(prev => ({
      ...prev,
      jobId: payload.job_id,
      message: payload.message,
      connectionState: 'connected',
      isConnected: true,
    }));
  }, []);

  /**
   * Handle progress updates
   */
  const handleProgressUpdate = useCallback((payload: ProcessingProgressPayload) => {
    setState(prev => ({
      ...prev,
      progress: payload.progress_percentage,
      currentStage: payload.current_stage,
      status: payload.status,
      message: payload.message,
      elapsedTime: payload.elapsed_time,
      remainingTime: payload.remaining_time,
    }));

    // Call user callback
    optionsRef.current.onProgressUpdate?.(payload);
  }, []);

  /**
   * Handle job completion
   */
  const handleJobCompleted = useCallback((payload: JobCompletedPayload) => {
    setState(prev => ({
      ...prev,
      status: payload.status,
      message: payload.message,
      progress: 100,
      isCompleted: true,
      outputFileUrl: payload.output_file_url || null,
      remainingTime: 0,
    }));

    // Call user callback
    optionsRef.current.onJobCompleted?.(payload);
  }, []);

  /**
   * Handle job failure
   */
  const handleJobFailed = useCallback((payload: JobFailedPayload) => {
    setState(prev => ({
      ...prev,
      status: payload.status,
      error: payload.error,
      isFailed: true,
      remainingTime: 0,
    }));

    // Call user callback
    optionsRef.current.onJobFailed?.(payload);
  }, []);

  /**
   * Handle connection errors
   */
  const handleError = useCallback((payload: ErrorPayload) => {
    setState(prev => ({
      ...prev,
      error: payload.error,
      connectionState: 'error',
      isConnected: false,
    }));

    // Call user callback
    optionsRef.current.onConnectionError?.(payload.error);
  }, []);

  /**
   * Handle connection errors
   */
  const handleConnectionError = useCallback((error: Event) => {
    const errorMessage = 'WebSocket connection error';
    setState(prev => ({
      ...prev,
      error: errorMessage,
      connectionState: 'error',
      isConnected: false,
    }));

    optionsRef.current.onConnectionError?.(errorMessage);
  }, []);

  /**
   * Handle connection closed
   */
  const handleConnectionClosed = useCallback((event: CloseEvent) => {
    setState(prev => ({
      ...prev,
      connectionState: 'disconnected',
      isConnected: false,
    }));
  }, []);

  /**
   * Connect to job progress updates
   */
  const connect = useCallback(async (jobId: string) => {
    try {
      // Reset state for new job
      setState(prev => ({
        ...initialState,
        jobId,
        connectionState: 'connecting',
      }));

      // Get or create connection
      connectionRef.current = webSocketManager.getConnection(jobId, optionsRef.current.wsConfig);
      
      // Connect with handlers
      await connectionRef.current.connect(jobId, {
        onConnectionEstablished: handleConnectionEstablished,
        onProcessingProgress: handleProgressUpdate,
        onJobCompleted: handleJobCompleted,
        onJobFailed: handleJobFailed,
        onError: handleError,
        onConnectionError: handleConnectionError,
        onConnectionClosed: handleConnectionClosed,
      });

    } catch (error) {
      console.error(`[JobProgress] Failed to connect to job ${jobId}:`, error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Connection failed',
        connectionState: 'error',
        isConnected: false,
      }));
      throw error;
    }
  }, [
    handleConnectionEstablished,
    handleProgressUpdate,
    handleJobCompleted,
    handleJobFailed,
    handleError,
    handleConnectionError,
    handleConnectionClosed,
  ]);

  /**
   * Disconnect from job progress updates
   */
  const disconnect = useCallback(() => {
    if (state.jobId && connectionRef.current) {
      webSocketManager.disconnectJob(state.jobId);
      connectionRef.current = null;
    }
    
    setState(prev => ({
      ...prev,
      connectionState: 'disconnected',
      isConnected: false,
    }));
  }, [state.jobId]);

  /**
   * Reconnect to current job
   */
  const reconnect = useCallback(async () => {
    if (state.jobId) {
      await connect(state.jobId);
    }
  }, [state.jobId, connect]);

  /**
   * Format progress as percentage
   */
  const formatProgress = useCallback((): string => {
    return `${Math.round(state.progress)}%`;
  }, [state.progress]);

  /**
   * Format remaining time
   */
  const formatTimeRemaining = useCallback((): string => {
    if (state.remainingTime <= 0) return '0s';
    
    const minutes = Math.floor(state.remainingTime / 60);
    const seconds = state.remainingTime % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  }, [state.remainingTime]);

  /**
   * Format elapsed time
   */
  const formatElapsedTime = useCallback((): string => {
    if (state.elapsedTime <= 0) return '0s';
    
    const minutes = Math.floor(state.elapsedTime / 60);
    const seconds = state.elapsedTime % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  }, [state.elapsedTime]);

  // Auto-connect if specified and jobId provided
  useEffect(() => {
    return () => {
      // Cleanup on unmount
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    disconnect,
    reconnect,
    state,
    formatProgress,
    formatTimeRemaining,
    formatElapsedTime,
  };
};

export default useJobProgress;