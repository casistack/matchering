/**
 * Settings API Service
 *
 * Frontend service for user model selection settings integration
 * Updated to match backend Pydantic schemas exactly
 */

import type {
  UserSettingsConfig,
  UserAnalytics,
  SystemStatus,
  ModelPreferences,
  AvailableModelInfo,
  UserSettingsProfile,
} from '@/types/settings';

/**
 * Settings API Configuration
 */
const SETTINGS_API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  API_VERSION: 'v1',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
} as const;

/**
 * Settings API Error Classes
 */
export class SettingsAPIError extends Error {
  public statusCode: number;
  public errorCode?: string;
  public field?: string;
  public requestId?: string;

  constructor(
    message: string,
    statusCode: number,
    errorCode?: string,
    field?: string,
    requestId?: string
  ) {
    super(message);
    this.name = 'SettingsAPIError';
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.field = field;
    this.requestId = requestId;
  }
}

export class SettingsNetworkError extends Error {
  public originalError?: Error;

  constructor(message: string, originalError?: Error) {
    super(message);
    this.name = 'SettingsNetworkError';
    this.originalError = originalError;
  }
}

/**
 * HTTP Client Helper
 */
class SettingsHttpClient {
  private baseURL: string;
  private timeout: number;

  constructor(baseURL: string, timeout: number) {
    this.baseURL = baseURL;
    this.timeout = timeout;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}/api/${SETTINGS_API_CONFIG.API_VERSION}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new SettingsAPIError(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData.code,
          errorData.field,
          errorData.requestId
        );
      }

      const data = await response.json();
      return data;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof SettingsAPIError) {
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new SettingsNetworkError('Request timeout', error);
        }
        throw new SettingsNetworkError('Network error', error);
      }

      throw new SettingsNetworkError('Unknown error occurred');
    }
  }

  async get<T>(
    endpoint: string,
    params?: Record<string, string>
  ): Promise<T> {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }
    return this.request<T>(url);
  }

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }
}

/**
 * Settings API Service
 */
export class SettingsAPIService {
  private client: SettingsHttpClient;

  constructor() {
    this.client = new SettingsHttpClient(
      SETTINGS_API_CONFIG.BASE_URL,
      SETTINGS_API_CONFIG.TIMEOUT
    );
  }

  /**
   * Get complete user configuration
   */
  async getUserConfiguration(anonymousId?: string): Promise<UserSettingsConfig> {
    const params = anonymousId ? { anonymous_id: anonymousId } : undefined;
    return await this.client.get<UserSettingsConfig>(
      '/settings/config',
      params
    );
  }

  /**
   * Update user preferences
   */
  async updatePreferences(
    preferences: Partial<ModelPreferences>,
    anonymousId?: string
  ): Promise<ModelPreferences> {
    const requestData = {
      ...preferences,
    };

    const params = anonymousId ? { anonymous_id: anonymousId } : undefined;
    const url = params ? `/settings/preferences?${new URLSearchParams(params).toString()}` : '/settings/preferences';
    
    const response = await this.client.put<{ profile: UserSettingsProfile }>(
      url,
      requestData
    );

    // Extract preferences from the profile response
    return {
      preferred_strategy: response.profile.preferred_strategy,
      ensemble_weights: response.profile.ensemble_weights,
      quality_preference: response.profile.quality_preference,
      enable_experimental: response.profile.enable_experimental,
      confidence_threshold: response.profile.confidence_threshold,
      max_processing_time: response.profile.max_processing_time,
      fallback_strategy: response.profile.fallback_strategy,
      custom_settings: response.profile.advanced_settings
    };
  }

  /**
   * Create new settings profile
   */
  async createProfile(
    name: string,
    description: string,
    preferences: ModelPreferences,
    anonymousId?: string
  ): Promise<UserSettingsProfile> {
    const requestData = {
      name,
      description,
      preferences: {
        preferred_strategy: preferences.preferred_strategy,
        ensemble_weights: preferences.ensemble_weights,
        quality_preference: preferences.quality_preference,
        enable_experimental: preferences.enable_experimental,
        confidence_threshold: preferences.confidence_threshold,
        max_processing_time: preferences.max_processing_time,
        fallback_strategy: preferences.fallback_strategy,
        custom_settings: preferences.custom_settings
      }
    };

    const params = anonymousId ? { anonymous_id: anonymousId } : undefined;
    const url = params ? `/settings/profiles?${new URLSearchParams(params).toString()}` : '/settings/profiles';
    
    return await this.client.post<UserSettingsProfile>(url, requestData);
  }

  /**
   * Get user profiles
   */
  async getUserProfiles(anonymousId?: string): Promise<UserSettingsProfile[]> {
    const params = anonymousId ? { anonymous_id: anonymousId } : undefined;
    return await this.client.get<UserSettingsProfile[]>(
      '/settings/profiles',
      params
    );
  }

  /**
   * Select active profile
   */
  async selectProfile(
    profileId: string,
    anonymousId?: string
  ): Promise<UserSettingsProfile> {
    const params = anonymousId ? { anonymous_id: anonymousId } : undefined;
    const url = params ? `/settings/profiles/${profileId}/select?${new URLSearchParams(params).toString()}` : `/settings/profiles/${profileId}/select`;
    
    const response = await this.client.put<{ active_profile: UserSettingsProfile }>(url, {});
    return response.active_profile;
  }

  /**
   * Delete profile
   */
  async deleteProfile(profileId: string, anonymousId?: string): Promise<void> {
    let url = `/settings/profiles/${profileId}`;
    if (anonymousId) {
      url += `?anonymous_id=${encodeURIComponent(anonymousId)}`;
    }
    await this.client.delete<{ success: boolean }>(url);
  }

  /**
   * Get available models information
   */
  async getAvailableModels(anonymousId?: string): Promise<AvailableModelInfo[]> {
    const params = anonymousId ? { anonymous_id: anonymousId } : undefined;
    return await this.client.get<AvailableModelInfo[]>(
      '/settings/models',
      params
    );
  }

  /**
   * Get user analytics
   */
  async getUserAnalytics(anonymousId?: string): Promise<UserAnalytics> {
    const params = anonymousId ? { anonymous_id: anonymousId } : undefined;
    return await this.client.get<UserAnalytics>(
      '/settings/analytics',
      params
    );
  }

  /**
   * Get system status
   */
  async getSystemStatus(): Promise<SystemStatus> {
    return await this.client.get<SystemStatus>('/settings/system/status');
  }

  /**
   * Reset to default preferences
   */
  async resetToDefaults(anonymousId?: string): Promise<ModelPreferences> {
    const params = anonymousId ? { anonymous_id: anonymousId } : undefined;
    const url = params ? `/settings/reset-defaults?${new URLSearchParams(params).toString()}` : '/settings/reset-defaults';
    
    const response = await this.client.post<{ profile: UserSettingsProfile }>(url, {});
    
    // Extract preferences from the profile response
    return {
      preferred_strategy: response.profile.preferred_strategy,
      ensemble_weights: response.profile.ensemble_weights,
      quality_preference: response.profile.quality_preference,
      enable_experimental: response.profile.enable_experimental,
      confidence_threshold: response.profile.confidence_threshold,
      max_processing_time: response.profile.max_processing_time,
      fallback_strategy: response.profile.fallback_strategy,
      custom_settings: response.profile.advanced_settings
    };
  }
}

/**
 * Singleton instance
 */
export const settingsAPI = new SettingsAPIService();

/**
 * Utility functions
 */
export const generateAnonymousId = (): string => {
  return `anon_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const getStoredAnonymousId = (): string | null => {
  try {
    return localStorage.getItem('matchering_anonymous_id');
  } catch {
    return null;
  }
};

export const setStoredAnonymousId = (id: string): void => {
  try {
    localStorage.setItem('matchering_anonymous_id', id);
  } catch {
    // Ignore localStorage errors
  }
};

export const ensureAnonymousId = (): string => {
  let anonymousId = getStoredAnonymousId();
  if (!anonymousId) {
    anonymousId = generateAnonymousId();
    setStoredAnonymousId(anonymousId);
  }
  return anonymousId;
};

/**
 * Error handling utilities
 */
export const isSettingsAPIError = (error: unknown): error is SettingsAPIError => {
  return error instanceof SettingsAPIError;
};

export const isSettingsNetworkError = (
  error: unknown
): error is SettingsNetworkError => {
  return error instanceof SettingsNetworkError;
};

export const formatSettingsError = (error: unknown): string => {
  if (isSettingsAPIError(error)) {
    return error.message;
  }

  if (isSettingsNetworkError(error)) {
    return 'Network error. Please check your connection and try again.';
  }

  return 'An unexpected error occurred. Please try again.';
};