/**
 * Settings Types for User Model Selection System
 * 
 * TypeScript definitions for frontend-backend API contract
 */

// Core enum types matching backend
export type ProcessingStrategy = 'auto' | 'performance' | 'quality' | 'custom';
export type ModelType = 'huggingface' | 'ast' | 'custom';
export type ModelName = 'distilhubert' | 'wav2vec2' | 'ast' | 'custom_cnn' | 'ensemble';

// Model preference configuration
export interface ModelPreferences {
  readonly preferredModels: ModelName[];
  readonly ensembleWeights: Record<ModelName, number>;
  readonly confidenceThreshold: number;
  readonly maxProcessingTime: number;
  readonly enableFallback: boolean;
  readonly fallbackStrategy: ProcessingStrategy;
  readonly customSettings: Record<string, unknown>;
}

// User settings profile
export interface UserSettingsProfile {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly isActive: boolean;
  readonly preferences: ModelPreferences;
  readonly createdAt: string;
  readonly updatedAt: string;
}

// Available model information
export interface AvailableModelInfo {
  readonly name: ModelName;
  readonly displayName: string;
  readonly type: ModelType;
  readonly description: string;
  readonly performanceMetrics: {
    readonly averageAccuracy: number;
    readonly averageProcessingTime: number;
    readonly totalUsage: number;
    readonly lastUpdated: string;
  };
  readonly isEnabled: boolean;
  readonly supportedGenres: string[];
  readonly memoryRequirement: number;
  readonly computeRequirement: string;
}

// Complete user configuration response
export interface UserSettingsConfig {
  readonly userId: string | null;
  readonly anonymousId: string | null;
  readonly preferences: ModelPreferences;
  readonly activeProfile: UserSettingsProfile | null;
  readonly profiles: UserSettingsProfile[];
  readonly availableModels: AvailableModelInfo[];
  readonly systemDefaults: ModelPreferences;
  readonly lastUpdated: string;
}

// Analytics data types
export interface ModelPerformanceMetrics {
  readonly modelName: ModelName;
  readonly accuracy: number;
  readonly processingTime: number;
  readonly genreAccuracy: Record<string, number>;
  readonly usageCount: number;
  readonly lastUsed: string;
}

export interface UserAnalytics {
  readonly totalProcessingJobs: number;
  readonly averageProcessingTime: number;
  readonly favoriteModels: ModelName[];
  readonly genreDistribution: Record<string, number>;
  readonly modelPerformance: ModelPerformanceMetrics[];
  readonly systemUsage: {
    readonly totalSessions: number;
    readonly averageSessionDuration: number;
    readonly lastActive: string;
  };
}

// System status information
export interface SystemStatus {
  readonly availableModels: ModelName[];
  readonly systemLoad: number;
  readonly queueLength: number;
  readonly averageProcessingTime: number;
  readonly modelHealth: Record<ModelName, boolean>;
  readonly lastUpdated: string;
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

// Component prop types
export interface ModelSelectorProps {
  readonly selectedModels: ModelName[];
  readonly availableModels: AvailableModelInfo[];
  readonly onSelectionChange: (models: ModelName[]) => void;
  readonly disabled?: boolean;
}

export interface EnsembleWeightControlProps {
  readonly weights: Record<ModelName, number>;
  readonly selectedModels: ModelName[];
  readonly onWeightChange: (weights: Record<ModelName, number>) => void;
  readonly disabled?: boolean;
}

export interface ProfileManagerProps {
  readonly profiles: UserSettingsProfile[];
  readonly activeProfile: UserSettingsProfile | null;
  readonly onProfileSelect: (profileId: string) => void;
  readonly onProfileCreate: (name: string, description: string, preferences: ModelPreferences) => void;
  readonly onProfileDelete: (profileId: string) => void;
  readonly disabled?: boolean;
}

export interface AnalyticsDashboardProps {
  readonly analytics: UserAnalytics | null;
  readonly systemStatus: SystemStatus | null;
  readonly isLoading: boolean;
}

// Form types
export interface ModelPreferencesFormData {
  preferredModels: ModelName[];
  ensembleWeights: Record<ModelName, number>;
  confidenceThreshold: number;
  maxProcessingTime: number;
  enableFallback: boolean;
  fallbackStrategy: ProcessingStrategy;
  customSettings: Record<string, unknown>;
}

export interface ProfileFormData {
  name: string;
  description: string;
  preferences: ModelPreferences;
}

// Error types
export interface SettingsError {
  readonly code: string;
  readonly message: string;
  readonly field?: string;
  readonly details?: Record<string, unknown>;
}

// Local storage keys
export const SETTINGS_STORAGE_KEYS = {
  ANONYMOUS_ID: 'matchering_anonymous_id',
  CACHED_CONFIG: 'matchering_cached_config',
  LAST_SYNC: 'matchering_last_sync',
} as const;

// Default values
export const DEFAULT_PREFERENCES: ModelPreferences = {
  preferredModels: ['ensemble'],
  ensembleWeights: {
    'distilhubert': 0.4,
    'wav2vec2': 0.3,
    'ast': 0.2,
    'custom_cnn': 0.1,
    'ensemble': 1.0
  },
  confidenceThreshold: 0.7,
  maxProcessingTime: 5000,
  enableFallback: true,
  fallbackStrategy: 'auto',
  customSettings: {}
};

export const PROCESSING_STRATEGIES: Record<ProcessingStrategy, string> = {
  auto: 'Auto - Fastest processing with good quality',
  performance: 'Performance - Optimized for speed',
  quality: 'Quality - Best results, slower processing',
  custom: 'Custom - User-defined settings'
};

export const MODEL_DISPLAY_NAMES: Record<ModelName, string> = {
  distilhubert: 'DistilHuBERT',
  wav2vec2: 'Wav2Vec2',
  ast: 'Audio Spectrogram Transformer',
  custom_cnn: 'Custom CNN',
  ensemble: 'Ensemble (Recommended)'
};