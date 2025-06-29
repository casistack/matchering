import type { AudioFormat, AudioFileMetadata, AudioProcessingResult } from './audio';
import type { ProcessingProgress } from './processing';
import type { FileUploadResponse, ProcessingJobRequest } from './api';

// Strict typing for custom hooks
export interface UseAudioUploadOptions {
  readonly maxFileSize: number; // bytes
  readonly allowedFormats: readonly AudioFormat[];
  readonly autoProcess: boolean;
  readonly onUploadProgress?: (progress: number) => void;
  readonly onUploadComplete?: (metadata: AudioFileMetadata) => void;
  readonly onUploadError?: (error: string) => void;
}

export interface UseAudioUploadReturn {
  readonly upload: (file: File) => Promise<FileUploadResponse>;
  readonly isUploading: boolean;
  readonly uploadProgress: number;
  readonly uploadError: string | null;
  readonly uploadedFiles: readonly AudioFileMetadata[];
  readonly clearError: () => void;
  readonly cancelUpload: () => void;
}

export interface UseProcessingOptions {
  readonly pollingInterval: number; // milliseconds
  readonly maxRetries: number;
  readonly onProgress?: (progress: ProcessingProgress) => void;
  readonly onComplete?: (result: AudioProcessingResult) => void;
  readonly onError?: (error: string) => void;
}

export interface UseProcessingReturn {
  readonly startProcessing: (request: ProcessingJobRequest) => Promise<void>;
  readonly cancelProcessing: (jobId: string) => Promise<void>;
  readonly isProcessing: boolean;
  readonly currentJob: ProcessingProgress | null;
  readonly processingError: string | null;
  readonly completedJobs: readonly AudioProcessingResult[];
}

// Audio player hook
export interface UseAudioPlayerOptions {
  readonly autoPlay?: boolean;
  readonly loop?: boolean;
  readonly volume?: number; // 0-1
}

export interface UseAudioPlayerReturn {
  readonly play: () => Promise<void>;
  readonly pause: () => void;
  readonly stop: () => void;
  readonly seek: (time: number) => void;
  readonly setVolume: (volume: number) => void;
  readonly isPlaying: boolean;
  readonly isPaused: boolean;
  readonly currentTime: number;
  readonly duration: number;
  readonly volume: number;
}