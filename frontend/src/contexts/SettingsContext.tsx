/**
 * Settings Context Provider
 * 
 * Global state management for user model selection settings
 */

import React, { createContext, useReducer, useCallback, useEffect } from 'react';
import type {
  SettingsContextValue,
  SettingsContextState,
  UserSettingsConfig,
  UserAnalytics,
  SystemStatus,
  ModelPreferences,
  UserSettingsProfile
} from '@/types/settings';
import {
  settingsAPI,
  ensureAnonymousId,
  formatSettingsError,
  isSettingsAPIError
} from '@/services/settings';

/**
 * Action Types
 */
type SettingsAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CONFIG'; payload: UserSettingsConfig }
  | { type: 'SET_ANALYTICS'; payload: UserAnalytics }
  | { type: 'SET_SYSTEM_STATUS'; payload: SystemStatus }
  | { type: 'UPDATE_PREFERENCES'; payload: ModelPreferences }
  | { type: 'ADD_PROFILE'; payload: UserSettingsProfile }
  | { type: 'SELECT_PROFILE'; payload: UserSettingsProfile }
  | { type: 'REMOVE_PROFILE'; payload: string }
  | { type: 'RESET_STATE' };

/**
 * Initial State
 */
const initialState: SettingsContextState = {
  config: null,
  analytics: null,
  systemStatus: null,
  isLoading: false,
  error: null,
};

/**
 * Settings Reducer
 */
const settingsReducer = (state: SettingsContextState, action: SettingsAction): SettingsContextState => {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
        error: action.payload ? null : state.error, // Clear error when starting new operation
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };

    case 'SET_CONFIG':
      return {
        ...state,
        config: action.payload,
        isLoading: false,
        error: null,
      };

    case 'SET_ANALYTICS':
      return {
        ...state,
        analytics: action.payload,
        error: null,
      };

    case 'SET_SYSTEM_STATUS':
      return {
        ...state,
        systemStatus: action.payload,
        error: null,
      };

    case 'UPDATE_PREFERENCES':
      if (!state.config) return state;
      return {
        ...state,
        config: {
          ...state.config,
          current_profile: {
            ...state.config.current_profile,
            preferred_strategy: action.payload.preferred_strategy,
            ensemble_weights: action.payload.ensemble_weights,
            quality_preference: action.payload.quality_preference,
            enable_experimental: action.payload.enable_experimental,
            confidence_threshold: action.payload.confidence_threshold,
            max_processing_time: action.payload.max_processing_time,
            fallback_strategy: action.payload.fallback_strategy,
            advanced_settings: action.payload.custom_settings,
            updated_at: new Date().toISOString(),
          },
        },
        error: null,
      };

    case 'ADD_PROFILE':
      if (!state.config) return state;
      return {
        ...state,
        config: {
          ...state.config,
          available_profiles: [...state.config.available_profiles, action.payload],
        },
        error: null,
      };

    case 'SELECT_PROFILE':
      if (!state.config) return state;
      return {
        ...state,
        config: {
          ...state.config,
          current_profile: action.payload,
        },
        error: null,
      };

    case 'REMOVE_PROFILE': {
      if (!state.config) return state;
      const updatedProfiles = state.config.available_profiles.filter(p => p.id !== action.payload);
      const isCurrentProfileDeleted = state.config.current_profile?.id === action.payload;
      
      return {
        ...state,
        config: {
          ...state.config,
          available_profiles: updatedProfiles,
          current_profile: isCurrentProfileDeleted 
            ? (updatedProfiles[0] || state.config.current_profile)
            : state.config.current_profile,
        },
        error: null,
      };
    }

    case 'RESET_STATE':
      return initialState;

    default:
      return state;
  }
};

/**
 * Settings Context
 */
// eslint-disable-next-line react-refresh/only-export-components
export const SettingsContext = createContext<SettingsContextValue | null>(null);

/**
 * Settings Provider Props
 */
interface SettingsProviderProps {
  children: React.ReactNode;
}

/**
 * Settings Provider Component
 */
export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(settingsReducer, initialState);

  /**
   * Error handling helper
   */
  const handleError = useCallback((error: unknown, context: string) => {
    console.error(`Settings ${context} error:`, error);
    
    let errorMessage = formatSettingsError(error);
    
    // Add context to error message
    if (isSettingsAPIError(error)) {
      errorMessage = `${context}: ${errorMessage}`;
    } else {
      errorMessage = `${context} failed: ${errorMessage}`;
    }
    
    dispatch({ type: 'SET_ERROR', payload: errorMessage });
  }, []);

  /**
   * Load user configuration
   */
  const loadUserConfig = useCallback(async (anonymousId?: string) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const id = anonymousId || ensureAnonymousId();
      console.log('🔧 Loading user config for:', id);
      const config = await settingsAPI.getUserConfiguration(id);
      console.log('🔧 Loaded config:', config);
      
      dispatch({ type: 'SET_CONFIG', payload: config });
    } catch (error) {
      console.error('🔧 Error loading config:', error);
      handleError(error, 'Load configuration');
    }
  }, [handleError]);

  /**
   * Update user preferences
   */
  const updatePreferences = useCallback(async (preferences: Partial<ModelPreferences>) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      console.log('🔧 ========== SETTINGS UPDATE ATTEMPT ==========');
      console.log('🔧 RAW_PREFERENCES_INPUT:', preferences);
      console.log('🔧 PREFERENCES_KEYS:', Object.keys(preferences));
      console.log('🔧 PREFERENCES_JSON:', JSON.stringify(preferences, null, 2));
      
      // Validate data before sending
      if (preferences.ensemble_weights) {
        const total = Object.values(preferences.ensemble_weights).reduce((sum, weight) => sum + weight, 0);
        console.log('🔧 ENSEMBLE_WEIGHTS_TOTAL:', total.toFixed(3));
        console.log('🔧 ENSEMBLE_WEIGHTS_VALID:', (total >= 0.9 && total <= 1.1));
      }
      
      if (preferences.confidence_threshold !== undefined) {
        console.log('🔧 CONFIDENCE_THRESHOLD:', preferences.confidence_threshold);
        console.log('🔧 CONFIDENCE_VALID:', (preferences.confidence_threshold >= 0.5 && preferences.confidence_threshold <= 0.95));
      }
      
      if (preferences.max_processing_time !== undefined) {
        console.log('🔧 MAX_PROCESSING_TIME:', preferences.max_processing_time);
        console.log('🔧 PROCESSING_TIME_VALID:', (preferences.max_processing_time >= 1000 && preferences.max_processing_time <= 10000));
      }
      
      const anonymousId = ensureAnonymousId();
      console.log('🔧 SENDING_TO_BACKEND_WITH_ID:', anonymousId);
      
      const updatedPreferences = await settingsAPI.updatePreferences(preferences, anonymousId);
      
      console.log('🔧 BACKEND_RESPONSE:', updatedPreferences);
      console.log('🔧 ========== SETTINGS UPDATE SUCCESS ==========');
      
      dispatch({ type: 'UPDATE_PREFERENCES', payload: updatedPreferences });
    } catch (error) {
      console.log('🔧 ========== SETTINGS UPDATE ERROR ==========');
      console.log('🔧 ERROR_OBJECT:', error);
      console.log('🔧 ERROR_MESSAGE:', error instanceof Error ? error.message : 'Unknown error');
      if (error instanceof Error && 'statusCode' in error) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        console.log('🔧 ERROR_STATUS_CODE:', (error as any).statusCode);
      }
      console.log('🔧 =======================================');
      
      handleError(error, 'Update preferences');
    }
  }, [handleError]);

  /**
   * Create new profile
   */
  const createProfile = useCallback(async (
    name: string,
    description: string,
    preferences: ModelPreferences
  ) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const anonymousId = ensureAnonymousId();
      const newProfile = await settingsAPI.createProfile(name, description, preferences, anonymousId);
      
      dispatch({ type: 'ADD_PROFILE', payload: newProfile });
    } catch (error) {
      handleError(error, 'Create profile');
    }
  }, [handleError]);

  /**
   * Select profile
   */
  const selectProfile = useCallback(async (profileId: string) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const anonymousId = ensureAnonymousId();
      const selectedProfile = await settingsAPI.selectProfile(profileId, anonymousId);
      
      dispatch({ type: 'SELECT_PROFILE', payload: selectedProfile });
    } catch (error) {
      handleError(error, 'Select profile');
    }
  }, [handleError]);

  /**
   * Delete profile
   */
  const deleteProfile = useCallback(async (profileId: string) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const anonymousId = ensureAnonymousId();
      await settingsAPI.deleteProfile(profileId, anonymousId);
      
      dispatch({ type: 'REMOVE_PROFILE', payload: profileId });
    } catch (error) {
      handleError(error, 'Delete profile');
    }
  }, [handleError]);

  /**
   * Load analytics
   */
  const loadAnalytics = useCallback(async () => {
    try {
      const anonymousId = ensureAnonymousId();
      const analytics = await settingsAPI.getUserAnalytics(anonymousId);
      
      dispatch({ type: 'SET_ANALYTICS', payload: analytics });
    } catch (error) {
      handleError(error, 'Load analytics');
    }
  }, [handleError]);

  /**
   * Load system status
   */
  const loadSystemStatus = useCallback(async () => {
    try {
      const systemStatus = await settingsAPI.getSystemStatus();
      
      dispatch({ type: 'SET_SYSTEM_STATUS', payload: systemStatus });
    } catch (error) {
      handleError(error, 'Load system status');
    }
  }, [handleError]);

  /**
   * Reset to defaults
   */
  const resetToDefaults = useCallback(async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const anonymousId = ensureAnonymousId();
      const defaultPreferences = await settingsAPI.resetToDefaults(anonymousId);
      
      dispatch({ type: 'UPDATE_PREFERENCES', payload: defaultPreferences });
    } catch (error) {
      handleError(error, 'Reset to defaults');
    }
  }, [handleError]);

  /**
   * Initialize settings on mount
   */
  useEffect(() => {
    loadUserConfig();
    loadAnalytics();
    loadSystemStatus();
  }, [loadUserConfig, loadAnalytics, loadSystemStatus]);

  /**
   * Context value
   */
  const contextValue: SettingsContextValue = {
    // State
    ...state,
    
    // Actions
    loadUserConfig,
    updatePreferences,
    createProfile,
    selectProfile,
    deleteProfile,
    loadAnalytics,
    loadSystemStatus,
    resetToDefaults,
  };

  return (
    <SettingsContext.Provider value={contextValue}>
      {children}
    </SettingsContext.Provider>
  );
};

export default SettingsContext;