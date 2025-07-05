/**
 * Model Preferences Panel Component
 * 
 * UI for configuring AI model selection and ensemble weights
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  FormControl,
  FormLabel,
  FormControlLabel,
  Checkbox,
  Slider,
  TextField,
  Button,
  Alert,
  Chip,
  Tooltip,
  IconButton,
  Divider,
  Switch,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  InfoRounded as InfoIcon,
  RestartAltRounded as ResetIcon,
  SaveRounded as SaveIcon,
  ExpandMoreRounded as ExpandMoreIcon,
  TuneRounded as TuneIcon,
  SpeedRounded as SpeedIcon,
  HighQualityRounded as QualityIcon,
  PsychologyRounded as BrainIcon,
} from '@mui/icons-material';
import { useSettings, useModelSelection } from '@/hooks/useSettings';
import type { 
  FallbackStrategy,
  ModelPreferences,
  AvailableModelInfo 
} from '@/types/settings';
import { 
  FALLBACK_STRATEGIES, 
  DEFAULT_PREFERENCES 
} from '@/types/settings';

/**
 * Model Card Component
 */
interface ModelCardProps {
  model: AvailableModelInfo;
  isSelected: boolean;
  weight: number;
  onSelectionChange: (selected: boolean) => void;
  onWeightChange: (weight: number) => void;
  disabled?: boolean;
}

const ModelCard: React.FC<ModelCardProps> = ({
  model,
  isSelected,
  weight,
  onSelectionChange,
  onWeightChange,
  disabled = false,
}) => {
  // Debug logging for ModelCard
  console.log(`🔧 STEP 3 - ModelCard Render [${model.name}]:`, { 
    id: model.id, 
    name: model.name, 
    isSelected, 
    weight: weight.toFixed(3), 
    disabled,
    timestamp: new Date().toISOString().split('T')[1]?.slice(0, 8) || 'N/A' // Just time
  });
  const getModelIcon = (modelId: string) => {
    switch (modelId) {
      case 'huggingface_ensemble':
        return <BrainIcon color="primary" />;
      case 'ast_model':
        return <QualityIcon color="success" />;
      case 'fallback_classifier':
        return <TuneIcon color="action" />;
      case 'distilhubert':
      case 'wav2vec2':
        return <SpeedIcon color="secondary" />;
      default:
        return <TuneIcon color="action" />;
    }
  };

  const getPerformanceColor = (accuracy: number) => {
    if (accuracy >= 0.9) return 'success';
    if (accuracy >= 0.8) return 'warning';
    return 'error';
  };

  return (
    <Card 
      variant={isSelected ? "elevation" : "outlined"}
      sx={{ 
        height: '100%',
        transition: 'all 0.2s ease-in-out',
        border: isSelected ? 2 : 1,
        borderColor: isSelected ? 'primary.main' : 'divider',
        backgroundColor: isSelected ? 'action.selected' : 'background.paper',
        '&:hover': {
          boxShadow: isSelected ? 4 : 2,
          backgroundColor: isSelected ? 'action.selected' : 'action.hover',
        },
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {getModelIcon(model.id)}
            <Typography variant="h6" component="h3">
              {model.name}
            </Typography>
          </Box>
          
          <FormControlLabel
            control={
              <Checkbox
                checked={isSelected}
                onChange={(e) => {
                  console.log(`🔧 ========== CHECKBOX CLICK [${model.name}] ==========`);
                  console.log(`🔧 CHECKBOX - User clicked:`, { 
                    modelName: model.name,
                    modelId: model.id,
                    previouslyChecked: isSelected,
                    nowChecked: e.target.checked,
                    weightBefore: weight.toFixed(3),
                    timestamp: new Date().toISOString()
                  });
                  onSelectionChange(e.target.checked);
                  console.log(`🔧 CHECKBOX - Event handler called for ${model.id}`);
                }}
                disabled={disabled}
                color="primary"
                sx={{
                  '& .MuiSvgIcon-root': {
                    fontSize: 28,
                  },
                  '&.Mui-checked': {
                    color: 'primary.main',
                  },
                }}
              />
            }
            label=""
            sx={{ m: 0 }}
          />
        </Box>

        <Typography variant="body2" color="text.secondary" paragraph>
          {model.description}
        </Typography>

        {/* Performance Metrics */}
        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="caption" color="text.secondary">
              Accuracy
            </Typography>
            <Chip
              label={`${(model.performance.accuracy * 100).toFixed(1)}%`}
              size="small"
              color={getPerformanceColor(model.performance.accuracy)}
              variant="outlined"
            />
          </Box>
          
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="caption" color="text.secondary">
              Avg. Processing Time
            </Typography>
            <Typography variant="caption">
              {(model.performance.average_processing_time / 1000).toFixed(1)}s
            </Typography>
          </Box>
        </Box>

        {/* Ensemble Weight Control */}
        {isSelected && (
          <Box>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              Ensemble Weight: {(weight * 100).toFixed(0)}%
            </Typography>
            <Slider
              value={weight}
              onChange={(_, value) => onWeightChange(value as number)}
              min={0.1}
              max={1.0}
              step={0.05}
              disabled={disabled}
              sx={{ mt: 1 }}
              marks={[
                { value: 0.1, label: '10%' },
                { value: 0.5, label: '50%' },
                { value: 1.0, label: '100%' },
              ]}
            />
          </Box>
        )}

        {/* Supported Genres */}
        <Box mt={2}>
          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
            Supported Genres ({model.performance.supported_genres.length})
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={0.5}>
            {model.performance.supported_genres.slice(0, 3).map((genre) => (
              <Chip
                key={genre}
                label={genre}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            ))}
            {model.performance.supported_genres.length > 3 && (
              <Chip
                label={`+${model.performance.supported_genres.length - 3} more`}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

/**
 * Model Preferences Panel Component
 */
const ModelPreferencesPanel: React.FC = () => {
  const { config, updatePreferences, resetToDefaults, isLoading } = useSettings();
  const {
    selectedModels,
    ensembleWeights,
    availableModels,
  } = useModelSelection();

  const [localPreferences, setLocalPreferences] = useState<Partial<ModelPreferences>>({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Debug logging - COMPREHENSIVE FLOW TRACKING
  console.log('🔧 ========== ModelPreferencesPanel RENDER ==========');
  console.log('🔧 STEP 1 - Raw Data:', {
    configExists: !!config,
    currentProfile: config?.current_profile ? 'EXISTS' : 'NULL',
    selectedModels,
    selectedModelsCount: selectedModels.length,
    ensembleWeights,
    ensembleWeightsKeys: Object.keys(ensembleWeights),
    availableModels: availableModels.map(m => ({ id: m.id, name: m.name })),
    availableModelsCount: availableModels.length,
    isLoading,
    hasUnsavedChanges,
    localPreferences: Object.keys(localPreferences).length > 0 ? localPreferences : 'EMPTY'
  });

  // Get current preferences
  const preferences = config?.current_profile || DEFAULT_PREFERENCES;

  // Get current values (local changes override saved preferences) - memoized to prevent unnecessary re-renders
  const currentPreferences = useMemo(() => ({ 
    preferred_strategy: preferences.preferred_strategy,
    ensemble_weights: preferences.ensemble_weights,
    quality_preference: preferences.quality_preference,
    enable_experimental: preferences.enable_experimental,
    confidence_threshold: preferences.confidence_threshold,
    max_processing_time: preferences.max_processing_time,
    fallback_strategy: preferences.fallback_strategy,
    custom_settings: 'advanced_settings' in preferences ? preferences.advanced_settings : {},
    ...localPreferences 
  }), [preferences, localPreferences]);

  const handleModelSelectionChange = useCallback((modelName: string, selected: boolean) => {
    console.log('🔧 ========== USER INTERACTION: MODEL SELECTION ==========');
    console.log('🔧 CLICK - Model Selection Change:', { 
      modelName, 
      selected, 
      timestamp: new Date().toISOString()
    });
    console.log('🔧 BEFORE - Current State:', {
      currentWeights: ensembleWeights,
      currentSelected: Object.keys(ensembleWeights),
      localPreferences: Object.keys(localPreferences).length > 0 ? localPreferences : 'EMPTY',
      hasUnsavedChanges
    });
    
    const currentWeights = currentPreferences.ensemble_weights || ensembleWeights;
    const newWeights: Record<string, number> = { ...currentWeights };
    
    if (selected) {
      // Adding a model - give it a default weight and rebalance
      const currentTotal = Object.values(newWeights).reduce((sum: number, w: number) => sum + w, 0);
      const defaultWeight = currentTotal > 0 ? 0.1 : 0.5; // Smaller if others exist
      newWeights[modelName] = defaultWeight;
      console.log('🔧 ACTION - Adding model with weight', defaultWeight);
      
      // Rebalance to sum to 1.0
      const newTotal = Object.values(newWeights).reduce((sum: number, w: number) => sum + w, 0);
      if (newTotal > 0) {
        Object.keys(newWeights).forEach(key => {
          newWeights[key] = (newWeights[key] || 0) / newTotal;
        });
      }
    } else {
      // Removing a model - delete it and rebalance remaining
      delete newWeights[modelName];
      console.log('🔧 ACTION - Removing model from weights');
      
      // Rebalance remaining weights to sum to 1.0
      const remainingKeys = Object.keys(newWeights);
      if (remainingKeys.length > 0) {
        const currentTotal = Object.values(newWeights).reduce((sum: number, w: number) => sum + w, 0);
        if (currentTotal > 0) {
          remainingKeys.forEach(key => {
            newWeights[key] = (newWeights[key] || 0) / currentTotal;
          });
        } else {
          // Distribute equally if all weights were 0
          const equalWeight = 1.0 / remainingKeys.length;
          remainingKeys.forEach(key => {
            newWeights[key] = equalWeight;
          });
        }
      }
    }

    console.log('🔧 AFTER - New State Will Be:', {
      newWeights,
      newSelected: Object.keys(newWeights),
      newTotal: Object.values(newWeights).reduce((sum: number, w: number) => sum + w, 0).toFixed(3)
    });

    setLocalPreferences(prev => {
      const updated = {
        ...prev,
        ensemble_weights: newWeights,
      };
      console.log('🔧 LOCAL_PREFERENCES_UPDATE:', updated);
      return updated;
    });
    setHasUnsavedChanges(true);
    console.log('🔧 ========== END USER INTERACTION ==========');
  }, [currentPreferences, ensembleWeights, hasUnsavedChanges, localPreferences]);

  const handleWeightChange = useCallback((modelName: string, weight: number) => {
    const currentWeights = currentPreferences.ensemble_weights || ensembleWeights;
    const newWeights: Record<string, number> = {
      ...currentWeights,
      [modelName]: weight,
    };

    console.log('🔧 WEIGHT_CHANGE:', {
      modelName,
      oldWeight: currentWeights[modelName] || 0,
      newWeight: weight,
      totalBefore: Object.values(currentWeights).reduce((sum: number, w: number) => sum + w, 0).toFixed(3),
      totalAfter: Object.values(newWeights).reduce((sum: number, w: number) => sum + w, 0).toFixed(3)
    });

    setLocalPreferences(prev => ({
      ...prev,
      ensemble_weights: newWeights,
    }));
    setHasUnsavedChanges(true);
  }, [currentPreferences, ensembleWeights]);

  const handleStrategyChange = useCallback((strategy: FallbackStrategy) => {
    console.log('🔧 STRATEGY_CHANGE:', { 
      oldStrategy: currentPreferences.fallback_strategy, 
      newStrategy: strategy 
    });
    
    setLocalPreferences(prev => ({
      ...prev,
      fallback_strategy: strategy,
    }));
    setHasUnsavedChanges(true);
  }, [currentPreferences.fallback_strategy]);

  const handlePreferenceChange = useCallback((field: keyof ModelPreferences, value: unknown) => {
    setLocalPreferences(prev => ({
      ...prev,
      [field]: value,
    }));
    setHasUnsavedChanges(true);
  }, []);

  const saveChanges = useCallback(async () => {
    if (!hasUnsavedChanges) return;

    await updatePreferences(localPreferences);
    setLocalPreferences({});
    setHasUnsavedChanges(false);
  }, [localPreferences, hasUnsavedChanges, updatePreferences]);

  const resetChanges = useCallback(() => {
    setLocalPreferences({});
    setHasUnsavedChanges(false);
  }, []);

  const resetToDefaultsHandler = useCallback(async () => {
    await resetToDefaults();
    setLocalPreferences({});
    setHasUnsavedChanges(false);
  }, [resetToDefaults]);

  // Use current ensemble weights (including local changes) for UI
  const currentEnsembleWeights = currentPreferences.ensemble_weights || ensembleWeights;
  const currentSelectedModels = Object.keys(currentEnsembleWeights);

  // Calculate total ensemble weight using current weights
  const totalWeight = Object.values(currentEnsembleWeights).reduce((sum: number, weight: number) => sum + weight, 0);
  const isWeightValid = Math.abs(totalWeight - 1.0) < 0.1;

  // Debug logging - CALCULATED STATE
  console.log('🔧 STEP 2 - Calculated State:', {
    currentEnsembleWeights,
    currentSelectedModels,
    currentSelectedModelsCount: currentSelectedModels.length,
    totalWeight: totalWeight.toFixed(3),
    isWeightValid,
    preferences: preferences.ensemble_weights ? 'HAS_WEIGHTS' : 'NO_WEIGHTS'
  });

  // Final debug log - render summary
  console.log('🔧 ========== RENDER COMPLETE - SUMMARY ==========');
  console.log('🔧 FINAL STATE:', {
    totalModelsAvailable: availableModels.length,
    totalModelsSelected: currentSelectedModels.length,
    selectedModelIds: currentSelectedModels,
    totalWeight: totalWeight.toFixed(3) + '%',
    isValid: isWeightValid,
    hasChanges: hasUnsavedChanges,
    timestamp: new Date().toISOString().split('T')[1]?.slice(0, 8) || 'N/A'
  });
  console.log('🔧 =====================================');

  return (
    <Box>
{/* Debug Info - Commented out for production */}
      {/* <Alert severity="info" sx={{ mb: 2 }}>
        <Typography variant="caption" component="div">
          <strong>🔧 Debug Info:</strong><br/>
          Available Models: {availableModels.length}<br/>
          Selected Models: [{currentSelectedModels.join(', ')}]<br/>
          Current Weights: {JSON.stringify(currentEnsembleWeights)}<br/>
          Original Weights: {JSON.stringify(ensembleWeights)}<br/>
          Has Unsaved Changes: {hasUnsavedChanges ? 'Yes' : 'No'}<br/>
          Loading: {isLoading ? 'Yes' : 'No'}
        </Typography>
      </Alert> */}

      {/* Action Buttons */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          Model Configuration
        </Typography>
        
        <Box display="flex" gap={1}>
          {hasUnsavedChanges && (
            <Button
              variant="outlined"
              onClick={resetChanges}
              disabled={isLoading}
              startIcon={<ResetIcon />}
            >
              Discard Changes
            </Button>
          )}
          
          <Button
            variant="contained"
            onClick={saveChanges}
            disabled={!hasUnsavedChanges || isLoading}
            startIcon={<SaveIcon />}
          >
            Save Changes
          </Button>
          
          <Tooltip title="Reset all settings to default values">
            <IconButton
              onClick={resetToDefaultsHandler}
              disabled={isLoading}
              color="error"
            >
              <ResetIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Ensemble Weight Validation */}
      {!isWeightValid && currentSelectedModels.length > 1 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            Ensemble weights should sum to approximately 100%. 
            Current total: <strong>{(totalWeight * 100).toFixed(1)}%</strong>
          </Typography>
        </Alert>
      )}

      {/* Model Selection Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {availableModels.map((model) => {
          const isModelSelected = currentSelectedModels.includes(model.id);
          const modelWeight = currentEnsembleWeights[model.id] || 0.1;
          
          // Debug logging for ModelCard creation
          console.log(`🔧 STEP 4 - Creating ModelCard [${model.name}]:`, {
            modelId: model.id,
            isInCurrentSelected: isModelSelected,
            currentSelectedModels,
            weightFromCurrent: modelWeight,
            currentEnsembleWeights: Object.keys(currentEnsembleWeights)
          });
          
          return (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={model.id}>
              <ModelCard
                model={model}
                isSelected={isModelSelected}
                weight={modelWeight}
                onSelectionChange={(selected) => handleModelSelectionChange(model.id, selected)}
                onWeightChange={(weight) => handleWeightChange(model.id, weight)}
                disabled={isLoading}
              />
            </Grid>
          );
        })}
      </Grid>

      {/* Advanced Settings */}
      <Accordion sx={{ mb: 3 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Advanced Settings</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            {/* Processing Strategy */}
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl component="fieldset" fullWidth>
                <FormLabel component="legend">Fallback Strategy</FormLabel>
                <Box mt={1}>
                  {Object.entries(FALLBACK_STRATEGIES).map(([strategy, description]) => (
                    <FormControlLabel
                      key={strategy}
                      control={
                        <Checkbox
                          checked={currentPreferences.fallback_strategy === strategy}
                          onChange={() => handleStrategyChange(strategy as FallbackStrategy)}
                          disabled={isLoading}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body2" fontWeight={500}>
                            {strategy.charAt(0).toUpperCase() + strategy.slice(1)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {description}
                          </Typography>
                        </Box>
                      }
                    />
                  ))}
                </Box>
              </FormControl>
            </Grid>

            {/* Confidence Threshold */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Typography variant="subtitle2" gutterBottom>
                Confidence Threshold: {(currentPreferences.confidence_threshold * 100).toFixed(0)}%
              </Typography>
              <Slider
                value={currentPreferences.confidence_threshold}
                onChange={(_, value) => handlePreferenceChange('confidence_threshold', value)}
                min={0.5}
                max={0.95}
                step={0.05}
                disabled={isLoading}
                marks={[
                  { value: 0.5, label: '50%' },
                  { value: 0.7, label: '70%' },
                  { value: 0.9, label: '90%' },
                ]}
              />
              <Typography variant="caption" color="text.secondary">
                Minimum confidence required for AI predictions
              </Typography>
            </Grid>

            {/* Max Processing Time */}
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                label="Max Processing Time (ms)"
                type="number"
                value={currentPreferences.max_processing_time}
                onChange={(e) => handlePreferenceChange('max_processing_time', parseInt(e.target.value))}
                disabled={isLoading}
                fullWidth
                inputProps={{ min: 1000, max: 10000, step: 500 }}
                helperText="Maximum time allowed for AI processing"
              />
            </Grid>

            {/* Enable Fallback */}
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={currentPreferences.enable_experimental}
                    onChange={(e) => handlePreferenceChange('enable_experimental', e.target.checked)}
                    disabled={isLoading}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">Enable Fallback Processing</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Use alternative methods if AI models fail
                    </Typography>
                  </Box>
                }
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Help Text */}
      <Alert severity="info" icon={<InfoIcon />}>
        <Typography variant="body2">
          <strong>Model Selection Tips:</strong>
          <br />
          • <strong>Ensemble</strong> mode combines multiple models for best accuracy
          <br />
          • <strong>DistilHuBERT</strong> and <strong>Wav2Vec2</strong> are optimized for speed
          <br />
          • <strong>AST</strong> provides the highest quality for complex audio
          <br />
          • Adjust ensemble weights based on your audio type and quality preferences
        </Typography>
      </Alert>
    </Box>
  );
};

export default ModelPreferencesPanel;