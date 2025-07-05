/**
 * Settings Hooks
 *
 * Custom hooks for accessing and managing settings state
 */

import { useContext, useCallback } from 'react';
import type { SettingsContextValue } from '@/types/settings';
import { SettingsContext } from '@/contexts/SettingsContext';

/**
 * Settings Hook
 */
export const useSettings = (): SettingsContextValue => {
  const context = useContext(SettingsContext);

  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }

  return context;
};

/**
 * Settings Hook with Loading State
 */
export const useSettingsWithLoading = () => {
  const settings = useSettings();

  return {
    ...settings,
    hasConfig: !!settings.config,
    hasAnalytics: !!settings.analytics,
    hasSystemStatus: !!settings.systemStatus,
    isInitializing: settings.isLoading && !settings.config,
  };
};

/**
 * Model Selection Hook
 */
export const useModelSelection = () => {
  const { config, updatePreferences, isLoading } = useSettings();

  const updateSelectedModels = useCallback(
    (modelNames: string[]) => {
      if (!config) return;

      const preferences = {
        ensemble_weights: Object.fromEntries(
          modelNames.map(name => [name, 1.0 / modelNames.length])
        ),
      };

      updatePreferences(preferences);
    },
    [config, updatePreferences]
  );

  const updateEnsembleWeights = useCallback(
    (weights: Record<string, number>) => {
      if (!config) return;

      const preferences = {
        ensemble_weights: weights,
      };

      updatePreferences(preferences);
    },
    [config, updatePreferences]
  );

  // Map old model names to new model IDs for backward compatibility
  const mapOldModelNames = (weights: Record<string, number>): Record<string, number> => {
    const nameMapping: Record<string, string> = {
      'huggingface': 'huggingface_ensemble',
      'ast': 'ast_model', 
      'fallback': 'fallback_classifier'
    };
    
    const mappedWeights: Record<string, number> = {};
    Object.entries(weights).forEach(([key, value]) => {
      const newKey = nameMapping[key] || key;
      mappedWeights[newKey] = value;
    });
    
    return mappedWeights;
  };

  const originalWeights = config?.current_profile?.ensemble_weights || {};
  const mappedWeights = mapOldModelNames(originalWeights);

  return {
    selectedModels: Object.keys(mappedWeights),
    ensembleWeights: mappedWeights,
    availableModels: config?.available_models || [],
    updateSelectedModels,
    updateEnsembleWeights,
    isLoading,
  };
};

/**
 * Profile Management Hook
 */
export const useProfileManagement = () => {
  const { config, createProfile, selectProfile, deleteProfile, isLoading } =
    useSettings();

  return {
    profiles: config?.available_profiles || [],
    activeProfile: config?.current_profile || null,
    createProfile,
    selectProfile,
    deleteProfile,
    isLoading,
  };
};
