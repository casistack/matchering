import { useState, useCallback } from 'react';
import type { 
  AudioFileMetadata, 
  AudioFormat, 
  UseAudioUploadOptions, 
  UseAudioUploadReturn,
  FileUploadResponse 
} from '@/types';

interface UploadState {
  readonly isUploading: boolean;
  readonly uploadProgress: number;
  readonly uploadError: string | null;
  readonly uploadedFiles: readonly AudioFileMetadata[];
}

const useAudioUpload = (options: UseAudioUploadOptions = {
  maxFileSize: 100 * 1024 * 1024, // 100MB
  allowedFormats: ['wav', 'mp3', 'flac', 'aiff'],
  autoProcess: false,
}): UseAudioUploadReturn => {
  const [state, setState] = useState<UploadState>({
    isUploading: false,
    uploadProgress: 0,
    uploadError: null,
    uploadedFiles: [],
  });

  const validateFile = useCallback((file: File): { valid: boolean; error?: string } => {
    // Check file size
    if (file.size > options.maxFileSize) {
      return {
        valid: false,
        error: `File size exceeds maximum allowed size of ${(options.maxFileSize / 1024 / 1024).toFixed(1)}MB`,
      };
    }

    // Check file format
    const extension = file.name.split('.').pop()?.toLowerCase() as AudioFormat;
    if (!options.allowedFormats.includes(extension)) {
      return {
        valid: false,
        error: `File format .${extension} is not supported`,
      };
    }

    // Check if file is actually an audio file
    if (!file.type.startsWith('audio/') && !['wav', 'mp3', 'flac', 'aiff'].includes(extension)) {
      return {
        valid: false,
        error: 'Selected file is not a valid audio file',
      };
    }

    return { valid: true };
  }, [options.maxFileSize, options.allowedFormats]);

  const analyzeAudioFile = useCallback(async (file: File): Promise<AudioFileMetadata> => {
    // This would typically use Web Audio API or a library to analyze the file
    // For now, we'll extract basic information and simulate analysis
    
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (): void => {
        try {
          const extension = file.name.split('.').pop()?.toLowerCase() as AudioFormat;
          
          // Generate a simple checksum (in real implementation, use crypto)
          const checksum = btoa(file.name + file.size + file.lastModified).substring(0, 32);
          
          const metadata: AudioFileMetadata = {
            filename: file.name,
            format: extension,
            sampleRate: 44100, // Default, would be extracted from actual analysis
            bitDepth: 16, // Default, would be extracted from actual analysis  
            channels: 2, // Default, would be extracted from actual analysis
            duration: 0, // Would be calculated from actual audio data
            fileSize: file.size,
            checksum,
          };
          
          resolve(metadata);
        } catch (analysisError) {
          const errorMessage = analysisError instanceof Error ? analysisError.message : 'Failed to analyze audio file';
          reject(new Error(errorMessage));
        }
      };
      
      reader.onerror = (): void => {
        reject(new Error('Failed to read audio file'));
      };
      
      // Read first few bytes to validate audio format
      reader.readAsArrayBuffer(file.slice(0, 1024));
    });
  }, []);

  const simulateUpload = useCallback(async (file: File): Promise<FileUploadResponse> => {
    // Simulate upload progress
    setState(prev => ({ ...prev, isUploading: true, uploadProgress: 0, uploadError: null }));
    
    try {
      // Simulate network delay and progress updates
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 100));
        setState(prev => ({ ...prev, uploadProgress: progress }));
        
        // Call progress callback
        options.onUploadProgress?.(progress);
      }
      
      // Analyze the file
      const metadata = await analyzeAudioFile(file);
      
      // Simulate server response
      const response: FileUploadResponse = {
        fileId: `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        uploadUrl: URL.createObjectURL(file), // Temporary URL for demo
        metadata,
        estimatedProcessingTime: Math.floor(metadata.duration * 0.1) || 30, // Estimate based on duration
      };
      
      // Update state with uploaded file
      setState(prev => ({
        ...prev,
        isUploading: false,
        uploadProgress: 100,
        uploadedFiles: [...prev.uploadedFiles, metadata],
      }));
      
      // Call completion callback
      options.onUploadComplete?.(metadata);
      
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setState(prev => ({
        ...prev,
        isUploading: false,
        uploadError: errorMessage,
      }));
      
      // Call error callback
      options.onUploadError?.(errorMessage);
      
      throw error;
    }
  }, [options, analyzeAudioFile]);

  const upload = useCallback(async (file: File): Promise<FileUploadResponse> => {
    // Clear previous errors
    setState(prev => ({ ...prev, uploadError: null }));
    
    // Validate file
    const validation = validateFile(file);
    if (!validation.valid) {
      const error = validation.error || 'Invalid file';
      setState(prev => ({ ...prev, uploadError: error }));
      options.onUploadError?.(error);
      throw new Error(error);
    }
    
    // Start upload
    return simulateUpload(file);
  }, [validateFile, simulateUpload, options]);

  const cancelUpload = useCallback((): void => {
    setState(prev => ({
      ...prev,
      isUploading: false,
      uploadProgress: 0,
      uploadError: null,
    }));
  }, []);

  const clearError = useCallback((): void => {
    setState(prev => ({ ...prev, uploadError: null }));
  }, []);

  return {
    upload,
    isUploading: state.isUploading,
    uploadProgress: state.uploadProgress,
    uploadError: state.uploadError,
    uploadedFiles: state.uploadedFiles,
    clearError,
    cancelUpload,
  };
};

export default useAudioUpload;