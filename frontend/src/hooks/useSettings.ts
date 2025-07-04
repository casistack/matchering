/**
 * Settings Hooks
 *
 * Custom hooks for accessing and managing settings state
 */

import { useContext, useCallback } from 'react';
import type { SettingsContextValue, ModelName } from '@/types/settings';
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
    (modelNames: ModelName[]) => {
      if (!config) return;

      const preferences = {
        ...config.preferences,
        preferredModels: modelNames,
      };

      updatePreferences(preferences);
    },
    [config, updatePreferences]
  );

  const updateEnsembleWeights = useCallback(
    (weights: Record<ModelName, number>) => {
      if (!config) return;

      const preferences = {
        ...config.preferences,
        ensembleWeights: weights,
      };

      updatePreferences(preferences);
    },
    [config, updatePreferences]
  );

  return {
    selectedModels: config?.preferences.preferredModels || [],
    ensembleWeights:
      config?.preferences.ensembleWeights || ({} as Record<ModelName, number>),
    availableModels: config?.availableModels || [],
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
    profiles: config?.profiles || [],
    activeProfile: config?.activeProfile || null,
    createProfile,
    selectProfile,
    deleteProfile,
    isLoading,
  };
};
