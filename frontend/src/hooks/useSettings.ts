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

  return {
    selectedModels: Object.keys(config?.current_profile?.ensemble_weights || {}),
    ensembleWeights: config?.current_profile?.ensemble_weights || {},
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
