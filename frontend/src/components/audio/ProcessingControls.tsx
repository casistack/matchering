import { useState, useCallback } from 'react';
import {
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Slider,
  Box,
  Button,
  Chip,
  Divider,
} from '@mui/material';
import { PlayArrow, Stop, Settings } from '@mui/icons-material';
import type { 
  ProcessingMode, 
  ProcessingSettings, 
  IntensityLevel, 
  EQStyle 
} from '@/types';

interface ProcessingControlsProps {
  readonly mode: ProcessingMode;
  readonly settings: ProcessingSettings;
  readonly onModeChange: (mode: ProcessingMode) => void;
  readonly onSettingsChange: (settings: ProcessingSettings) => void;
  readonly onStartProcessing?: () => void;
  readonly onStopProcessing?: () => void;
  readonly isProcessing?: boolean;
  readonly disabled?: boolean;
}

const ProcessingControls = ({
  mode,
  settings,
  onModeChange,
  onSettingsChange,
  onStartProcessing,
  onStopProcessing,
  isProcessing = false,
  disabled = false,
}: ProcessingControlsProps): JSX.Element => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSettingChange = useCallback(
    <K extends keyof ProcessingSettings>(
      key: K,
      value: ProcessingSettings[K]
    ): void => {
      const newSettings: ProcessingSettings = {
        ...settings,
        [key]: value,
      };
      onSettingsChange(newSettings);
    },
    [settings, onSettingsChange]
  );

  const getModeDescription = (selectedMode: ProcessingMode): string => {
    switch (selectedMode) {
      case 'auto':
        return 'AI analyzes your track and automatically applies optimal mastering settings';
      case 'reference':
        return 'Traditional Matchering - match your track to a reference using advanced DSP';
      case 'hybrid':
        return 'AI suggests reference tracks, then applies traditional Matchering processing';
      default:
        return '';
    }
  };

  const getModeColor = (selectedMode: ProcessingMode): 'primary' | 'secondary' | 'default' => {
    switch (selectedMode) {
      case 'auto':
        return 'primary';
      case 'reference':
        return 'secondary';
      case 'hybrid':
        return 'default';
      default:
        return 'default';
    }
  };

  return (
    <Card sx={{ width: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Settings />
          Processing Settings
        </Typography>

        {/* Processing Mode Selection */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Processing Mode
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            {(['auto', 'reference', 'hybrid'] as const).map((modeOption) => (
              <Chip
                key={modeOption}
                label={modeOption.charAt(0).toUpperCase() + modeOption.slice(1)}
                variant={mode === modeOption ? 'filled' : 'outlined'}
                color={mode === modeOption ? getModeColor(modeOption) : 'default'}
                onClick={() => onModeChange(modeOption)}
                disabled={disabled}
                sx={{ textTransform: 'capitalize' }}
              />
            ))}
          </Box>
          <Typography variant="caption" color="text.secondary">
            {getModeDescription(mode)}
          </Typography>
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Basic Settings */}
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 3 }}>
          {/* Intensity */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Intensity</InputLabel>
            <Select
              value={settings.intensity}
              onChange={(e) => handleSettingChange('intensity', e.target.value as IntensityLevel)}
              disabled={disabled}
            >
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
            </Select>
          </FormControl>

          {/* EQ Style */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>EQ Style</InputLabel>
            <Select
              value={settings.eqStyle}
              onChange={(e) => handleSettingChange('eqStyle', e.target.value as EQStyle)}
              disabled={disabled}
            >
              <MenuItem value="bright">Bright</MenuItem>
              <MenuItem value="balanced">Balanced</MenuItem>
              <MenuItem value="warm">Warm</MenuItem>
              <MenuItem value="auto">Auto</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Advanced Settings Toggle */}
        <Box sx={{ mb: 2 }}>
          <Button
            variant="text"
            size="small"
            onClick={() => setShowAdvanced(!showAdvanced)}
            disabled={disabled}
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Settings
          </Button>
        </Box>

        {/* Advanced Settings */}
        {showAdvanced && (
          <Box sx={{ mb: 3 }}>
            {/* Preserve Dynamics */}
            <FormControlLabel
              control={
                <Switch
                  checked={settings.preserveDynamics}
                  onChange={(e) => handleSettingChange('preserveDynamics', e.target.checked)}
                  disabled={disabled}
                />
              }
              label="Preserve Dynamics"
              sx={{ mb: 2 }}
            />

            {/* Target Loudness */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                Target Loudness (LUFS): {settings.targetLoudness}
              </Typography>
              <Slider
                value={settings.targetLoudness}
                onChange={(_, value) => handleSettingChange('targetLoudness', value as number)}
                min={-23}
                max={-6}
                step={0.5}
                marks={[
                  { value: -23, label: '-23' },
                  { value: -16, label: '-16' },
                  { value: -12, label: '-12' },
                  { value: -6, label: '-6' },
                ]}
                disabled={disabled}
                valueLabelDisplay="auto"
              />
              <Typography variant="caption" color="text.secondary">
                Industry standards: Streaming (-16 to -14), Radio (-12 to -8), Club (-6 to -3)
              </Typography>
            </Box>
          </Box>
        )}

        <Divider sx={{ mb: 3 }} />

        {/* Processing Controls */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          {!isProcessing ? (
            <Button
              variant="contained"
              size="large"
              startIcon={<PlayArrow />}
              onClick={onStartProcessing}
              disabled={disabled}
              sx={{ minWidth: 150 }}
            >
              Start Processing
            </Button>
          ) : (
            <Button
              variant="outlined"
              size="large"
              startIcon={<Stop />}
              onClick={onStopProcessing}
              color="error"
              sx={{ minWidth: 150 }}
            >
              Stop Processing
            </Button>
          )}
        </Box>

        {/* Settings Summary */}
        <Box sx={{ mt: 3, p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Current Settings:</strong> {mode.charAt(0).toUpperCase() + mode.slice(1)} mode, 
            {settings.intensity} intensity, {settings.eqStyle} EQ, 
            Target: {settings.targetLoudness} LUFS
            {settings.preserveDynamics && ', Preserve dynamics'}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ProcessingControls;