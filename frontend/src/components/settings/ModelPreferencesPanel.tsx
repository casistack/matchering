/**
 * Model Preferences Panel Component
 * 
 * UI for configuring AI model selection and ensemble weights
 */

import React, { useState, useCallback } from 'react';
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
  ModelName, 
  ProcessingStrategy, 
  ModelPreferences,
  AvailableModelInfo 
} from '@/types/settings';
import { 
  PROCESSING_STRATEGIES, 
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
  const getModelIcon = (modelName: ModelName) => {
    switch (modelName) {
      case 'ensemble':
        return <BrainIcon color="primary" />;
      case 'distilhubert':
      case 'wav2vec2':
        return <SpeedIcon color="secondary" />;
      case 'ast':
        return <QualityIcon color="success" />;
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
        '&:hover': {
          boxShadow: isSelected ? 4 : 2,
        },
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {getModelIcon(model.name)}
            <Typography variant="h6" component="h3">
              {model.displayName}
            </Typography>
          </Box>
          
          <FormControlLabel
            control={
              <Checkbox
                checked={isSelected}
                onChange={(e) => onSelectionChange(e.target.checked)}
                disabled={disabled}
                color="primary"
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
              label={`${(model.performanceMetrics.averageAccuracy * 100).toFixed(1)}%`}
              size="small"
              color={getPerformanceColor(model.performanceMetrics.averageAccuracy)}
              variant="outlined"
            />
          </Box>
          
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="caption" color="text.secondary">
              Avg. Processing Time
            </Typography>
            <Typography variant="caption">
              {model.performanceMetrics.averageProcessingTime.toFixed(1)}s
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
            Supported Genres ({model.supportedGenres.length})
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={0.5}>
            {model.supportedGenres.slice(0, 3).map((genre) => (
              <Chip
                key={genre}
                label={genre}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            ))}
            {model.supportedGenres.length > 3 && (
              <Chip
                label={`+${model.supportedGenres.length - 3} more`}
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

  // Get current preferences
  const preferences = config?.preferences || DEFAULT_PREFERENCES;

  const handleModelSelectionChange = useCallback((modelName: ModelName, selected: boolean) => {
    const newSelectedModels = selected
      ? [...selectedModels, modelName]
      : selectedModels.filter(name => name !== modelName);

    setLocalPreferences(prev => ({
      ...prev,
      preferredModels: newSelectedModels,
    }));
    setHasUnsavedChanges(true);
  }, [selectedModels]);

  const handleWeightChange = useCallback((modelName: ModelName, weight: number) => {
    const newWeights: Record<ModelName, number> = {
      ...ensembleWeights,
      [modelName]: weight,
    };

    setLocalPreferences(prev => ({
      ...prev,
      ensembleWeights: newWeights,
    }));
    setHasUnsavedChanges(true);
  }, [ensembleWeights]);

  const handleStrategyChange = useCallback((strategy: ProcessingStrategy) => {
    setLocalPreferences(prev => ({
      ...prev,
      fallbackStrategy: strategy,
    }));
    setHasUnsavedChanges(true);
  }, []);

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

  // Calculate total ensemble weight
  const totalWeight = Object.values(ensembleWeights).reduce((sum: number, weight: number) => sum + weight, 0);
  const isWeightValid = Math.abs(totalWeight - 1.0) < 0.1;

  // Get current values (local changes override saved preferences)
  const currentPreferences = { ...preferences, ...localPreferences };

  return (
    <Box>
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
      {!isWeightValid && selectedModels.length > 1 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            Ensemble weights should sum to approximately 100%. 
            Current total: <strong>{(totalWeight * 100).toFixed(1)}%</strong>
          </Typography>
        </Alert>
      )}

      {/* Model Selection Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {availableModels.map((model) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={model.name}>
            <ModelCard
              model={model}
              isSelected={selectedModels.includes(model.name)}
              weight={ensembleWeights[model.name] || 0.1}
              onSelectionChange={(selected) => handleModelSelectionChange(model.name, selected)}
              onWeightChange={(weight) => handleWeightChange(model.name, weight)}
              disabled={isLoading}
            />
          </Grid>
        ))}
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
                  {Object.entries(PROCESSING_STRATEGIES).map(([strategy, description]) => (
                    <FormControlLabel
                      key={strategy}
                      control={
                        <Checkbox
                          checked={currentPreferences.fallbackStrategy === strategy}
                          onChange={() => handleStrategyChange(strategy as ProcessingStrategy)}
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
                Confidence Threshold: {(currentPreferences.confidenceThreshold * 100).toFixed(0)}%
              </Typography>
              <Slider
                value={currentPreferences.confidenceThreshold}
                onChange={(_, value) => handlePreferenceChange('confidenceThreshold', value)}
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
                value={currentPreferences.maxProcessingTime}
                onChange={(e) => handlePreferenceChange('maxProcessingTime', parseInt(e.target.value))}
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
                    checked={currentPreferences.enableFallback}
                    onChange={(e) => handlePreferenceChange('enableFallback', e.target.checked)}
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