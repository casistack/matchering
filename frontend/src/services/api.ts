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
  TIMEOUT: 30000, // 30 seconds
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
    
    try {
      const requestOptions: RequestInit = {
        ...options,
        headers: {
          ...this.defaultHeaders,
          ...options.headers,
        },
        signal: options.signal || AbortSignal.timeout(API_CONFIG.TIMEOUT),
      };

      console.log(`[API] ${options.method || 'GET'} ${url}`);

      const response = await fetch(url, requestOptions);

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

      if (!responseData.success && responseData.error) {
        throw new APIClientError(
          responseData.error,
          response.status,
          'API_ERROR',
          responseData.requestId
        );
      }

      return responseData;

    } catch (error) {
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
    return apiClient.post<ProcessingJobResponse>('/processing/jobs', request);
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
  client: apiClient
};