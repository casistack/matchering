/**
 * React Hook for Processing Job Management
 * 
 * Manages the complete processing workflow including job creation, progress tracking,
 * and result retrieval using both REST API and WebSocket connections.
 */

import { useState, useCallback, useRef } from 'react';
import { processingAPI, APIClientError, NetworkClientError } from '@/services/api';
import { useJobProgress } from '@/hooks/useJobProgress';
import type { 
  ProcessingMode, 
  ProcessingSettings,
  ProcessingJobRequest,
  ProcessingJobResponse 
} from '@/types';

/**
 * Processing Job State
 */
export interface ProcessingJobState {
  jobId: string | null;
  status: 'idle' | 'creating' | 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  currentStage: string;
  message: string;
  elapsedTime: number;
  remainingTime: number;
  queuePosition: number;
  estimatedCompletion: string | null;
  error: string | null;
  outputFileUrl: string | null;
  isProcessing: boolean;
  canCancel: boolean;
}

/**
 * Processing Job Hook Options
 */
export interface UseProcessingJobOptions {
  onJobStarted?: (jobId: string, response: ProcessingJobResponse) => void;
  onProgressUpdate?: (progress: number, stage: string) => void;
  onJobCompleted?: (jobId: string, outputUrl: string | null) => void;
  onJobFailed?: (jobId: string, error: string) => void;
  onJobCancelled?: (jobId: string) => void;
  autoConnectWebSocket?: boolean;
}

/**
 * Processing Job Hook Return Type
 */
export interface UseProcessingJobReturn {
  // Job management
  startJob: (fileId: string, mode: ProcessingMode, settings: ProcessingSettings, referenceFileId?: string) => Promise<string>;
  cancelJob: () => Promise<void>;
  
  // State
  state: ProcessingJobState;
  
  // WebSocket connection state
  connectionState: string;
  isConnected: boolean;
  
  // Utilities
  formatProgress: () => string;
  formatTimeRemaining: () => string;
  formatElapsedTime: () => string;
  reset: () => void;
}

/**
 * Initial state for processing job
 */
const initialState: ProcessingJobState = {
  jobId: null,
  status: 'idle',
  progress: 0,
  currentStage: '',
  message: '',
  elapsedTime: 0,
  remainingTime: 0,
  queuePosition: 0,
  estimatedCompletion: null,
  error: null,
  outputFileUrl: null,
  isProcessing: false,
  canCancel: false,
};

/**
 * Hook for managing processing jobs
 */
export const useProcessingJob = (options: UseProcessingJobOptions = {}): UseProcessingJobReturn => {
  const [state, setState] = useState<ProcessingJobState>(initialState);
  const optionsRef = useRef(options);

  // Update options ref when options change
  optionsRef.current = options;

  // WebSocket progress tracking
  const jobProgress = useJobProgress({
    onProgressUpdate: (progress) => {
      setState(prev => ({
        ...prev,
        progress: progress.progress_percentage,
        currentStage: progress.current_stage,
        message: progress.message,
        elapsedTime: progress.elapsed_time,
        remainingTime: progress.remaining_time,
        status: progress.status === 'completed' ? 'completed' : 'processing',
      }));
      
      optionsRef.current.onProgressUpdate?.(progress.progress_percentage, progress.current_stage);
    },
    
    onJobCompleted: (completion) => {
      setState(prev => ({
        ...prev,
        status: 'completed',
        progress: 100,
        message: completion.message,
        outputFileUrl: completion.output_file_url || null,
        isProcessing: false,
        canCancel: false,
        remainingTime: 0,
      }));
      
      optionsRef.current.onJobCompleted?.(completion.job_id, completion.output_file_url || null);
    },
    
    onJobFailed: (failure) => {
      setState(prev => ({
        ...prev,
        status: 'failed',
        error: failure.error,
        isProcessing: false,
        canCancel: false,
        remainingTime: 0,
      }));
      
      optionsRef.current.onJobFailed?.(failure.job_id, failure.error);
    },
    
    onConnectionError: (error) => {
      setState(prev => ({
        ...prev,
        error: `Connection error: ${error}`,
      }));
    },
  });

  /**
   * Start a new processing job
   */
  const startJob = useCallback(async (
    fileId: string,
    mode: ProcessingMode,
    settings: ProcessingSettings,
    referenceFileId?: string
  ): Promise<string> => {
    try {
      // Reset state
      setState(initialState);
      setState(prev => ({ ...prev, status: 'creating' }));

      // Create job request
      const jobRequest: ProcessingJobRequest = {
        fileId,
        mode,
        settings,
        referenceFileId,
      };

      // Call API to create job
      const response = await processingAPI.createJob(jobRequest);

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to create processing job');
      }

      const jobData = response.data;

      // Update state with job information
      setState(prev => ({
        ...prev,
        jobId: jobData.jobId,
        status: 'queued',
        queuePosition: jobData.queuePosition,
        estimatedCompletion: jobData.estimatedCompletion,
        isProcessing: true,
        canCancel: true,
        message: `Job queued (position ${jobData.queuePosition})`,
      }));

      // Connect to WebSocket for progress updates if enabled
      if (options.autoConnectWebSocket !== false) {
        try {
          await jobProgress.connect(jobData.jobId);
        } catch (wsError) {
          console.warn('Failed to connect to WebSocket, will poll for updates:', wsError);
        }
      }

      // Call user callback
      optionsRef.current.onJobStarted?.(jobData.jobId, jobData);

      return jobData.jobId;

    } catch (error) {
      let errorMessage = 'Failed to start processing job';
      
      if (error instanceof APIClientError) {
        errorMessage = `API Error: ${error.message}`;
      } else if (error instanceof NetworkClientError) {
        errorMessage = `Network Error: ${error.message}`;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      setState(prev => ({
        ...prev,
        status: 'failed',
        error: errorMessage,
        isProcessing: false,
        canCancel: false,
      }));

      throw error;
    }
  }, [options.autoConnectWebSocket, jobProgress]);

  /**
   * Cancel the current processing job
   */
  const cancelJob = useCallback(async (): Promise<void> => {
    if (!state.jobId || !state.canCancel) {
      return;
    }

    try {
      setState(prev => ({ ...prev, message: 'Cancelling job...', canCancel: false }));

      // Call API to cancel job
      const response = await processingAPI.cancelJob?.(state.jobId);

      if (response && !response.success) {
        throw new Error(response.error || 'Failed to cancel job');
      }

      // Update state
      setState(prev => ({
        ...prev,
        status: 'cancelled',
        isProcessing: false,
        canCancel: false,
        message: 'Job cancelled',
      }));

      // Disconnect WebSocket
      jobProgress.disconnect();

      // Call user callback
      optionsRef.current.onJobCancelled?.(state.jobId);

    } catch (error) {
      let errorMessage = 'Failed to cancel job';
      
      if (error instanceof APIClientError) {
        errorMessage = `API Error: ${error.message}`;
      } else if (error instanceof NetworkClientError) {
        errorMessage = `Network Error: ${error.message}`;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      setState(prev => ({
        ...prev,
        error: errorMessage,
        canCancel: true, // Allow retry
      }));

      throw error;
    }
  }, [state.jobId, state.canCancel, jobProgress]);

  /**
   * Reset the job state
   */
  const reset = useCallback(() => {
    jobProgress.disconnect();
    setState(initialState);
  }, [jobProgress]);

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

  return {
    startJob,
    cancelJob,
    state,
    connectionState: jobProgress.state.connectionState,
    isConnected: jobProgress.state.isConnected,
    formatProgress,
    formatTimeRemaining,
    formatElapsedTime,
    reset,
  };
};

export default useProcessingJob;