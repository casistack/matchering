/**
 * Settings Types for User Model Selection System
 * 
 * TypeScript definitions matching backend Pydantic schemas exactly
 */

// Core enum types matching backend exactly
export type ModelSelectionStrategy = 'auto' | 'performance' | 'quality' | 'custom';
export type QualityPreference = 'fast' | 'balanced' | 'quality';
export type FallbackStrategy = 'strict' | 'graceful' | 'aggressive';
export type ModelType = 'huggingface' | 'ast' | 'custom';
export type ModelName = 'huggingface' | 'ast' | 'distilhubert' | 'wav2vec2' | 'custom_cnn' | 'ensemble';

// Backend model performance schema
export interface ModelPerformanceInfo {
  readonly average_processing_time: number;
  readonly accuracy: number;
  readonly memory_usage: number;
  readonly gpu_required: boolean;
  readonly supported_genres: string[];
}

// Backend model preferences schema (matches ModelPreferencesSchema)
export interface ModelPreferences {
  readonly preferred_strategy: ModelSelectionStrategy;
  readonly ensemble_weights: Record<string, number>;
  readonly quality_preference: QualityPreference;
  readonly enable_experimental: boolean;
  readonly confidence_threshold: number;
  readonly max_processing_time: number;
  readonly fallback_strategy: FallbackStrategy;
  readonly custom_settings: Record<string, unknown>;
}

// Backend user settings profile schema (matches UserSettingsProfileSchema)
export interface UserSettingsProfile {
  readonly id: string;
  readonly name: string;
  readonly description: string | null;
  readonly preferred_strategy: ModelSelectionStrategy;
  readonly ensemble_weights: Record<string, number>;
  readonly quality_preference: QualityPreference;
  readonly enable_experimental: boolean;
  readonly confidence_threshold: number;
  readonly max_processing_time: number;
  readonly fallback_strategy: FallbackStrategy;
  readonly advanced_settings: Record<string, unknown>;
  readonly feature_flags: Record<string, unknown>;
  readonly is_default: boolean;
  readonly is_custom: boolean;
  readonly is_system_profile: boolean;
  readonly usage_count: number;
  readonly created_at: string;
  readonly updated_at: string;
  readonly last_used: string | null;
}

// Backend available model info schema (matches AvailableModelInfoSchema)
export interface AvailableModelInfo {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly type: ModelType;
  readonly performance: ModelPerformanceInfo;
  readonly is_available: boolean;
  readonly requirements: string[];
  readonly version: string;
  readonly provider: string;
}

// Backend settings config response (matches SettingsConfigResponse)
export interface UserSettingsConfig {
  readonly current_profile: UserSettingsProfile;
  readonly available_profiles: UserSettingsProfile[];
  readonly available_models: AvailableModelInfo[];
  readonly system_defaults: ModelPreferences;
  readonly feature_flags: Record<string, boolean>;
}

// Backend analytics schema (matches UserSettingsAnalyticsSchema)
export interface UserAnalytics {
  readonly total_processing_jobs: number;
  readonly average_processing_time: number;
  readonly most_used_model: string | null;
  readonly model_usage_distribution: Record<string, number>;
  readonly quality_ratings: Record<string, number>;
  readonly performance_trends: Record<string, number[]>;
  readonly period_days: number;
}

// Backend system status schema (matches SystemStatusResponse)
export interface SystemStatus {
  readonly available_models_count: number;
  readonly active_users_count: number;
  readonly cache_hit_rate: number;
  readonly average_response_time: number;
  readonly feature_flags: Record<string, boolean>;
  readonly last_updated: string;
}

// Request/Response types for API calls
export interface UpdatePreferencesRequest {
  readonly preferences: Partial<ModelPreferences>;
  readonly anonymousId?: string;
}

export interface CreateProfileRequest {
  readonly name: string;
  readonly description: string;
  readonly preferences: ModelPreferences;
  readonly anonymousId?: string;
}

export interface SelectProfileRequest {
  readonly profileId: string;
  readonly anonymousId?: string;
}

// API Response wrappers
export interface SettingsResponse<T> {
  readonly success: boolean;
  readonly data: T | null;
  readonly error: string | null;
  readonly timestamp: string;
  readonly requestId: string;
}

// Settings Context types
export interface SettingsContextState {
  readonly config: UserSettingsConfig | null;
  readonly analytics: UserAnalytics | null;
  readonly systemStatus: SystemStatus | null;
  readonly isLoading: boolean;
  readonly error: string | null;
}

export interface SettingsContextActions {
  readonly loadUserConfig: (anonymousId?: string) => Promise<void>;
  readonly updatePreferences: (preferences: Partial<ModelPreferences>) => Promise<void>;
  readonly createProfile: (name: string, description: string, preferences: ModelPreferences) => Promise<void>;
  readonly selectProfile: (profileId: string) => Promise<void>;
  readonly deleteProfile: (profileId: string) => Promise<void>;
  readonly loadAnalytics: () => Promise<void>;
  readonly loadSystemStatus: () => Promise<void>;
  readonly resetToDefaults: () => Promise<void>;
}

export interface SettingsContextValue extends SettingsContextState, SettingsContextActions {}

// Local storage keys
export const SETTINGS_STORAGE_KEYS = {
  ANONYMOUS_ID: 'matchering_anonymous_id',
  CACHED_CONFIG: 'matchering_cached_config',
  LAST_SYNC: 'matchering_last_sync',
} as const;

// Default values matching backend defaults
export const DEFAULT_PREFERENCES: ModelPreferences = {
  preferred_strategy: 'auto',
  ensemble_weights: {
    'huggingface': 0.7,
    'ast': 0.25,
    'fallback': 0.05
  },
  quality_preference: 'balanced',
  enable_experimental: false,
  confidence_threshold: 0.6,
  max_processing_time: 5000,
  fallback_strategy: 'graceful',
  custom_settings: {}
};

export const PROCESSING_STRATEGIES: Record<ModelSelectionStrategy, string> = {
  auto: 'Auto - Fastest processing with good quality',
  performance: 'Performance - Optimized for speed',
  quality: 'Quality - Best results, slower processing',
  custom: 'Custom - User-defined settings'
};

export const QUALITY_PREFERENCES: Record<QualityPreference, string> = {
  fast: 'Fast - Quick processing',
  balanced: 'Balanced - Good quality and speed',
  quality: 'Quality - Best results'
};

export const FALLBACK_STRATEGIES: Record<FallbackStrategy, string> = {
  strict: 'Strict - Fail if models unavailable',
  graceful: 'Graceful - Use fallback methods',
  aggressive: 'Aggressive - Try all available options'
};

export const MODEL_DISPLAY_NAMES: Record<string, string> = {
  huggingface: 'HuggingFace Transformer',
  ast: 'Audio Spectrogram Transformer',
  distilhubert: 'DistilHuBERT',
  wav2vec2: 'Wav2Vec2',
  custom_cnn: 'Custom CNN',
  ensemble: 'Ensemble (Recommended)'
};