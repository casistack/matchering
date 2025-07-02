/**
 * React Hook for Processing Job Management
 * 
 * Manages the complete processing workflow including job creation, progress tracking,
 * and result retrieval using both REST API and WebSocket connections.
 */

import { useState, useCallback, useRef } from 'react';
import { processingAPI, hybridAI, APIClientError, NetworkClientError } from '@/services/api';
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
  startJob: (fileIdOrFile: string | File, mode: ProcessingMode, settings: ProcessingSettings, referenceFileId?: string) => Promise<string>;
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
    fileIdOrFile: string | File,
    mode: ProcessingMode,
    settings: ProcessingSettings,
    referenceFileId?: string
  ): Promise<string> => {
    try {
      // Reset state
      setState(initialState);
      setState(prev => ({ ...prev, status: 'creating' }));

      // Handle different processing modes
      let response: any;
      
      if (mode === 'hybrid' && fileIdOrFile instanceof File) {
        // Use hybrid AI API for hybrid mode
        const hybridOptions = {
          modelPreference: 'auto',
          processingMode: mode,
          intensityLevel: settings.intensity,
          eqStyle: settings.eqStyle,  // Add the missing eq_style field
          preserveDynamics: settings.preserveDynamics,
          targetLoudnessLufs: settings.targetLoudness,
          referenceFileId,
        };
        
        console.log('[ProcessingJob] Starting hybrid AI processing with options:', hybridOptions);
        response = await hybridAI.processHybrid(fileIdOrFile, hybridOptions);
        console.log('[ProcessingJob] Hybrid AI response:', response);
      } else {
        // Use regular processing API for auto and reference modes
        const fileId = typeof fileIdOrFile === 'string' ? fileIdOrFile : '';
        const jobRequest: ProcessingJobRequest = {
          fileId,
          mode,
          settings,
          referenceFileId,
        };

        response = await processingAPI.createJob(jobRequest);
      }

      console.log('[ProcessingJob] API Response:', response);
      
      if (!response.success || !response.data) {
        const errorMsg = response.error || 'Failed to create processing job';
        console.error('[ProcessingJob] Job creation failed:', errorMsg);
        throw new Error(errorMsg);
      }

      const jobData = response.data;
      
      // Handle different response formats
      let jobId: string;
      let queuePosition = 1;
      let estimatedCompletion: string | null = null;
      
      if (mode === 'hybrid') {
        // Hybrid AI response format
        jobId = jobData.job_id;
        estimatedCompletion = `${Math.round(jobData.estimated_completion_time)} seconds`;
      } else {
        // Regular processing response format
        jobId = jobData.jobId;
        queuePosition = jobData.queuePosition || 1;
        estimatedCompletion = jobData.estimatedCompletion;
      }

      // Update state with job information
      setState(prev => ({
        ...prev,
        jobId: jobId,
        status: 'queued',
        queuePosition: queuePosition,
        estimatedCompletion: estimatedCompletion,
        isProcessing: true,
        canCancel: true,
        message: `Job queued (position ${queuePosition})`,
      }));

      // Connect to WebSocket for progress updates if enabled
      if (options.autoConnectWebSocket !== false) {
        try {
          console.log(`[ProcessingJob] Connecting to WebSocket for job: ${jobId}`);
          await jobProgress.connect(jobId);
          console.log(`[ProcessingJob] WebSocket connected successfully for job: ${jobId}`);
        } catch (wsError) {
          console.warn('[ProcessingJob] Failed to connect to WebSocket, will poll for updates:', wsError);
        }
      }

      // Call user callback
      optionsRef.current.onJobStarted?.(jobId, jobData);

      return jobId;

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