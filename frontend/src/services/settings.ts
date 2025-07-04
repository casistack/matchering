/**
 * Settings API Service
 *
 * Frontend service for user model selection settings integration
 */

import type {
  UserSettingsConfig,
  UpdatePreferencesRequest,
  CreateProfileRequest,
  SelectProfileRequest,
  UserAnalytics,
  SystemStatus,
  SettingsResponse,
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
  ): Promise<SettingsResponse<T>> {
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
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
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
  ): Promise<SettingsResponse<T>> {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }
    return this.request<T>(url);
  }

  async post<T>(endpoint: string, data: unknown): Promise<SettingsResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data: unknown): Promise<SettingsResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<SettingsResponse<T>> {
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
    const response = await this.client.get<UserSettingsConfig>(
      '/settings/config',
      params
    );

    if (!response.success || !response.data) {
      throw new SettingsAPIError(
        response.error || 'Failed to fetch user configuration',
        500,
        'FETCH_CONFIG_FAILED'
      );
    }

    return response.data;
  }

  /**
   * Update user preferences
   */
  async updatePreferences(
    preferences: Partial<ModelPreferences>,
    anonymousId?: string
  ): Promise<ModelPreferences> {
    const requestData: UpdatePreferencesRequest = {
      preferences,
      anonymousId,
    };

    const response = await this.client.put<ModelPreferences>(
      '/settings/preferences',
      requestData
    );

    if (!response.success || !response.data) {
      throw new SettingsAPIError(
        response.error || 'Failed to update preferences',
        500,
        'UPDATE_PREFERENCES_FAILED'
      );
    }

    return response.data;
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
    const requestData: CreateProfileRequest = {
      name,
      description,
      preferences,
      anonymousId,
    };

    const response = await this.client.post<UserSettingsProfile>(
      '/settings/profiles',
      requestData
    );

    if (!response.success || !response.data) {
      throw new SettingsAPIError(
        response.error || 'Failed to create profile',
        500,
        'CREATE_PROFILE_FAILED'
      );
    }

    return response.data;
  }

  /**
   * Get user profiles
   */
  async getUserProfiles(anonymousId?: string): Promise<UserSettingsProfile[]> {
    const params = anonymousId ? { anonymous_id: anonymousId } : undefined;
    const response = await this.client.get<UserSettingsProfile[]>(
      '/settings/profiles',
      params
    );

    if (!response.success || !response.data) {
      throw new SettingsAPIError(
        response.error || 'Failed to fetch profiles',
        500,
        'FETCH_PROFILES_FAILED'
      );
    }

    return response.data;
  }

  /**
   * Select active profile
   */
  async selectProfile(
    profileId: string,
    anonymousId?: string
  ): Promise<UserSettingsProfile> {
    const requestData: SelectProfileRequest = {
      profileId,
      anonymousId,
    };

    const response = await this.client.put<UserSettingsProfile>(
      `/settings/profiles/${profileId}/select`,
      requestData
    );

    if (!response.success || !response.data) {
      throw new SettingsAPIError(
        response.error || 'Failed to select profile',
        500,
        'SELECT_PROFILE_FAILED'
      );
    }

    return response.data;
  }

  /**
   * Delete profile
   */
  async deleteProfile(profileId: string, anonymousId?: string): Promise<void> {
    let url = `/settings/profiles/${profileId}`;
    if (anonymousId) {
      url += `?anonymous_id=${encodeURIComponent(anonymousId)}`;
    }
    const response = await this.client.delete<void>(url);

    if (!response.success) {
      throw new SettingsAPIError(
        response.error || 'Failed to delete profile',
        500,
        'DELETE_PROFILE_FAILED'
      );
    }
  }

  /**
   * Get available models information
   */
  async getAvailableModels(anonymousId?: string): Promise<AvailableModelInfo[]> {
    const params = anonymousId ? { anonymous_id: anonymousId } : undefined;
    const response = await this.client.get<AvailableModelInfo[]>(
      '/settings/models',
      params
    );

    if (!response.success || !response.data) {
      throw new SettingsAPIError(
        response.error || 'Failed to fetch available models',
        500,
        'FETCH_MODELS_FAILED'
      );
    }

    return response.data;
  }

  /**
   * Get user analytics
   */
  async getUserAnalytics(anonymousId?: string): Promise<UserAnalytics> {
    const params = anonymousId ? { anonymous_id: anonymousId } : undefined;
    const response = await this.client.get<UserAnalytics>(
      '/settings/analytics',
      params
    );

    if (!response.success || !response.data) {
      throw new SettingsAPIError(
        response.error || 'Failed to fetch analytics',
        500,
        'FETCH_ANALYTICS_FAILED'
      );
    }

    return response.data;
  }

  /**
   * Get system status
   */
  async getSystemStatus(): Promise<SystemStatus> {
    const response = await this.client.get<SystemStatus>('/settings/system/status');

    if (!response.success || !response.data) {
      throw new SettingsAPIError(
        response.error || 'Failed to fetch system status',
        500,
        'FETCH_STATUS_FAILED'
      );
    }

    return response.data;
  }

  /**
   * Reset to default preferences
   */
  async resetToDefaults(anonymousId?: string): Promise<ModelPreferences> {
    const requestData = { anonymousId };
    const response = await this.client.post<ModelPreferences>(
      '/settings/reset-defaults',
      requestData
    );

    if (!response.success || !response.data) {
      throw new SettingsAPIError(
        response.error || 'Failed to reset to defaults',
        500,
        'RESET_DEFAULTS_FAILED'
      );
    }

    return response.data;
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
