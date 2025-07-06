import type { AudioFileMetadata, AudioProcessingResult } from './audio';
import type { ProcessingMode, ProcessingSettings, ProcessingProgress, JobStatus } from './processing';

// Strict API request/response types
export interface APIResponse<T = unknown> {
  readonly success: boolean;
  readonly data: T | null;
  readonly error: string | null;
  readonly timestamp: string; // ISO 8601
  readonly requestId: string;
}

export interface FileUploadRequest {
  readonly file: File;
  readonly processingMode: ProcessingMode;
  readonly settings?: ProcessingSettings;
}

export interface FileUploadResponse {
  readonly fileId: string;
  readonly uploadUrl: string;
  readonly metadata: AudioFileMetadata;
  readonly estimatedProcessingTime: number; // seconds
}

export interface ProcessingJobRequest {
  readonly input_file_id: string;
  readonly processing_mode: ProcessingMode;
  readonly settings: ProcessingSettings;
  readonly reference_file_id?: string; // For reference mode
  readonly priority?: number; // Optional priority (1-10, 1=highest, 10=lowest)
}

export interface ProcessingJobResponse {
  readonly jobId: string;
  readonly status: JobStatus;
  readonly queuePosition: number;
  readonly estimatedCompletion: string; // ISO 8601
}

// Error types
export interface APIError {
  readonly code: string;
  readonly message: string;
  readonly details?: Record<string, unknown>;
}

// API configuration
export interface APIConfig {
  readonly baseUrl: string;
  readonly timeout: number;
  readonly maxRetries: number;
}

// API client interface
export interface APIClient {
  readonly uploadFile: (request: FileUploadRequest) => Promise<APIResponse<FileUploadResponse>>;
  readonly startProcessing: (request: ProcessingJobRequest) => Promise<APIResponse<ProcessingJobResponse>>;
  readonly getProgress: (jobId: string) => Promise<APIResponse<ProcessingProgress>>;
  readonly getResult: (jobId: string) => Promise<APIResponse<AudioProcessingResult>>;
  readonly cancelJob: (jobId: string) => Promise<APIResponse<void>>;
}