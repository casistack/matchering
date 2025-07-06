/**
 * API Client Service for Enhanced Matchering Frontend
 * 
 * Type-safe HTTP client for backend communication with error handling and retry logic.
 */

import type {
  APIResponse,
  FileUploadResponse,
  ProcessingJobRequest,
  ProcessingJobResponse
} from '@/types/api';

/**
 * API Configuration
 */
const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  API_VERSION: 'v1',
  TIMEOUT: 120000, // 120 seconds for large file uploads
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
} as const;

/**
 * API Client Error Types
 */
export class APIClientError extends Error {
  public statusCode: number;
  public errorCode?: string;
  public requestId?: string;

  constructor(
    message: string,
    statusCode: number,
    errorCode?: string,
    requestId?: string
  ) {
    super(message);
    this.name = 'APIClientError';
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.requestId = requestId;
  }
}

export class NetworkClientError extends Error {
  public originalError?: Error;

  constructor(message: string, originalError?: Error) {
    super(message);
    this.name = 'NetworkClientError';
    this.originalError = originalError;
  }
}

/**
 * Enhanced API Client with comprehensive error handling and type safety
 */
class APIClient {
  private baseURL: string;
  private defaultHeaders: HeadersInit;

  constructor() {
    this.baseURL = `${API_CONFIG.BASE_URL}/api/${API_CONFIG.API_VERSION}`;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  /**
   * Sleep utility for retry delays
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Core HTTP request method with retry logic and error handling
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<APIResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);
    
    try {
      // For FormData, don't include default Content-Type header
      const isFormData = options.body instanceof FormData;
      const headers = isFormData 
        ? { ...options.headers }
        : { ...this.defaultHeaders, ...options.headers };
      
      const requestOptions: RequestInit = {
        ...options,
        headers,
        signal: options.signal || controller.signal,
      };

      console.log(`[API] ${options.method || 'GET'} ${url}`);
      
      // Log FormData contents for debugging (without file contents)
      if (isFormData && options.body instanceof FormData) {
        const formDataEntries: string[] = [];
        for (const [key, value] of options.body.entries()) {
          if (value instanceof File) {
            formDataEntries.push(`${key}: File(${value.name}, ${value.size} bytes)`);
          } else {
            formDataEntries.push(`${key}: ${value}`);
          }
        }
        console.log(`[API] FormData: ${formDataEntries.join(', ')}`);
      }

      const response = await fetch(url, requestOptions);
      
      // Clear the timeout
      clearTimeout(timeoutId);
      
      // Debug log the response
      console.log(`[API] Response status: ${response.status}, ok: ${response.ok}`);
      console.log(`[API] Response headers:`, Object.fromEntries(response.headers.entries()));

      // Handle non-JSON responses (like file downloads)
      const contentType = response.headers.get('Content-Type') || '';
      if (!contentType.includes('application/json')) {
        if (response.ok) {
          return {
            success: true,
            data: response as unknown as T,
            error: null,
            timestamp: new Date().toISOString(),
            requestId: response.headers.get('X-Request-ID') || 'unknown'
          };
        } else {
          throw new APIClientError(
            `HTTP ${response.status}: ${response.statusText}`,
            response.status,
            'HTTP_ERROR',
            response.headers.get('X-Request-ID') || undefined
          );
        }
      }

      const responseData: APIResponse<T> = await response.json();

      if (!response.ok) {
        const errorMessage = responseData.error || `HTTP ${response.status}: ${response.statusText}`;
        throw new APIClientError(
          errorMessage,
          response.status,
          'API_ERROR',
          responseData.requestId
        );
      }

      // Check for API-level errors even with 200 status
      if (responseData.success === false) {
        const errorMessage = responseData.error || 'Unknown API error';
        throw new APIClientError(
          errorMessage,
          response.status,
          'API_ERROR',
          responseData.requestId
        );
      }

      return responseData;

    } catch (error) {
      // Clear the timeout on error
      clearTimeout(timeoutId);
      
      console.error(`[API] Error ${options.method || 'GET'} ${url}:`, error);

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = new NetworkClientError('Network connection failed', error);
        
        // Retry on network errors
        if (retryCount < API_CONFIG.RETRY_ATTEMPTS) {
          await this.sleep(API_CONFIG.RETRY_DELAY * Math.pow(2, retryCount));
          return this.request<T>(endpoint, options, retryCount + 1);
        }
        
        throw networkError;
      }

      // Handle timeout errors
      if (error instanceof DOMException && error.name === 'TimeoutError') {
        if (retryCount < API_CONFIG.RETRY_ATTEMPTS) {
          await this.sleep(API_CONFIG.RETRY_DELAY * Math.pow(2, retryCount));
          return this.request<T>(endpoint, options, retryCount + 1);
        }
        
        throw new NetworkClientError('Request timeout', error);
      }

      // Re-throw API errors as-is
      if (error instanceof APIClientError) {
        throw error;
      }

      // Handle other errors
      throw new NetworkClientError('Unknown network error', error instanceof Error ? error : new Error(String(error)));
    }
  }

  /**
   * POST request with FormData (for file uploads)
   */
  async postForm<T>(endpoint: string, formData: FormData): Promise<APIResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type for FormData - let browser set it with boundary
        'Accept': 'application/json',
      },
    });
  }

  /**
   * POST request with JSON body
   */
  async post<T>(endpoint: string, data?: unknown): Promise<APIResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string): Promise<APIResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }
}

// Create singleton API client instance
const apiClient = new APIClient();

/**
 * Audio File Management API
 */
export const audioAPI = {
  /**
   * Upload an audio file for processing
   */
  async uploadFile(file: File, options: {
    processingMode?: 'auto' | 'reference' | 'hybrid';
    autoAnalyze?: boolean;
  } = {}): Promise<APIResponse<FileUploadResponse>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('processing_mode', options.processingMode || 'auto');
    formData.append('auto_analyze', options.autoAnalyze !== false ? 'true' : 'false');
    
    return apiClient.postForm<FileUploadResponse>('/audio/upload', formData);
  },
};

/**
 * Processing Job Management API
 */
export const processingAPI = {
  /**
   * Create a new processing job
   */
  async createJob(request: ProcessingJobRequest): Promise<APIResponse<ProcessingJobResponse>> {
    // Route based on processing mode
    if (request.processing_mode === 'hybrid') {
      // Use hybrid AI endpoint for hybrid mode
      const formData = new FormData();
      
      // Note: This assumes we have the actual file, but we might need to adjust
      // the API to work with file IDs. For now, we'll fallback to regular processing
      return apiClient.post<ProcessingJobResponse>('/processing/jobs', request);
    }
    
    return apiClient.post<ProcessingJobResponse>('/processing/jobs', request);
  },

  /**
   * Cancel a processing job
   */
  async cancelJob(jobId: string): Promise<APIResponse<void>> {
    return apiClient.post<void>(`/processing/jobs/${jobId}/cancel`);
  },
};

/**
 * Hybrid AI Processing API
 */
export const hybridAI = {
  /**
   * Check hybrid AI service health
   */
  async healthCheck(): Promise<APIResponse<{ status: string; service: string; available_models: Record<string, boolean> }>> {
    return apiClient.get('/hybrid-ai/health');
  },

  /**
   * Get available AI models
   */
  async getAvailableModels(): Promise<APIResponse<{ models: Record<string, any>; total_available: number }>> {
    return apiClient.get('/hybrid-ai/available-models');
  },

  /**
   * Extract hybrid features from audio file
   */
  async extractFeatures(file: File, options: {
    includeModelFeatures?: boolean;
    includeCustomFeatures?: boolean;
    cacheResult?: boolean;
  } = {}): Promise<APIResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('include_model_features', options.includeModelFeatures !== false ? 'true' : 'false');
    formData.append('include_custom_features', options.includeCustomFeatures !== false ? 'true' : 'false');
    formData.append('cache_result', options.cacheResult !== false ? 'true' : 'false');
    
    return apiClient.postForm('/hybrid-ai/extract-hybrid-features', formData);
  },

  /**
   * Select optimal model for audio content
   */
  async selectModel(file: File): Promise<APIResponse<{
    recommended_model: string;
    model_confidence: number;
    audio_characteristics: any;
    available_models: string[];
    selection_reasoning: string;
  }>> {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient.postForm('/hybrid-ai/select-model', formData);
  },

  /**
   * Predict mastering parameters using hybrid AI
   */
  async predictParameters(file: File, options: {
    modelPreference?: string;
    userStyle?: string;
    processingMode?: string;
    intensityLevel?: string;
    preserveDynamics?: boolean;
    targetLoudnessLufs?: number;
  } = {}): Promise<APIResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options.modelPreference) {
      formData.append('model_preference', options.modelPreference);
    }
    if (options.userStyle) {
      formData.append('user_style', options.userStyle);
    }
    if (options.processingMode) {
      formData.append('processing_mode', options.processingMode);
    }
    if (options.intensityLevel) {
      formData.append('intensity_level', options.intensityLevel);
    }
    if (options.preserveDynamics !== undefined) {
      formData.append('preserve_dynamics', options.preserveDynamics ? 'true' : 'false');
    }
    if (options.targetLoudnessLufs !== undefined) {
      formData.append('target_loudness_lufs', options.targetLoudnessLufs.toString());
    }
    
    return apiClient.postForm('/hybrid-ai/predict-parameters', formData);
  },

  /**
   * Process audio using hybrid AI mastering
   */
  async processHybrid(file: File, options: {
    modelPreference?: string;
    userStyle?: string;
    processingMode?: string;
    intensityLevel?: string;
    eqStyle?: string;
    preserveDynamics?: boolean;
    targetLoudnessLufs?: number;
    referenceFileId?: string;
  } = {}): Promise<APIResponse<{
    success: boolean;
    job_id: string;
    processing_mode: string;
    model_used: string;
    estimated_completion_time: number;
    audio_characteristics: any;
    predicted_parameters: any;
    processing_metadata: any;
  }>> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options.modelPreference) {
      formData.append('model_preference', options.modelPreference);
    }
    if (options.userStyle) {
      formData.append('user_style', options.userStyle);
    }
    if (options.processingMode) {
      formData.append('processing_mode', options.processingMode);
    }
    if (options.intensityLevel) {
      formData.append('intensity_level', options.intensityLevel);
    }
    if (options.eqStyle) {
      formData.append('eq_style', options.eqStyle);
    }
    if (options.preserveDynamics !== undefined) {
      formData.append('preserve_dynamics', options.preserveDynamics ? 'true' : 'false');
    }
    if (options.targetLoudnessLufs !== undefined) {
      formData.append('target_loudness_lufs', options.targetLoudnessLufs.toString());
    }
    if (options.referenceFileId) {
      formData.append('reference_file_id', options.referenceFileId);
    }
    
    return apiClient.postForm('/hybrid-ai/process-hybrid', formData);
  },

  /**
   * Get model performance metrics
   */
  async getModelPerformance(): Promise<APIResponse<{
    model_stats: Record<string, any>;
    system_stats: any;
    cache_stats: any;
    recommendations: string[];
  }>> {
    return apiClient.get('/hybrid-ai/model-performance');
  },
};

/**
 * Export the main API client for advanced usage
 */
export { apiClient };

/**
 * Default export with all API modules
 */
export default {
  audio: audioAPI,
  processing: processingAPI,
  hybridAI: hybridAI,
  client: apiClient
};