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
import { PlayArrow, Stop, Settings, Info, Speed, Engineering, Psychology, Science } from '@mui/icons-material';
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

  const getModeDisplayName = (selectedMode: ProcessingMode): string => {
    switch (selectedMode) {
      case 'auto':
        return 'AI Auto-Master';
      case 'reference':
        return 'Reference-Based';
      case 'hybrid':
        return 'AI + Matchering';
      case 'advanced':
        return 'Multi-Model AI';
      default:
        return selectedMode.charAt(0).toUpperCase() + selectedMode.slice(1);
    }
  };

  const getModeDescription = (selectedMode: ProcessingMode): string => {
    switch (selectedMode) {
      case 'auto':
        return 'Fast, intelligent mastering using custom AI models - perfect for quick projects';
      case 'reference':
        return 'Professional reference matching using proven DSP - requires reference track';
      case 'hybrid':
        return 'AI creates virtual reference for traditional processing - best of both worlds';
      case 'advanced':
        return 'Cutting-edge ensemble AI using multiple pre-trained models - research quality';
      default:
        return '';
    }
  };

  const getModeColor = (selectedMode: ProcessingMode): 'primary' | 'secondary' | 'default' | 'success' => {
    switch (selectedMode) {
      case 'auto':
        return 'primary';
      case 'reference':
        return 'secondary';
      case 'hybrid':
        return 'success';
      case 'advanced':
        return 'default';
      default:
        return 'default';
    }
  };

  const getModeIcon = (selectedMode: ProcessingMode): JSX.Element => {
    switch (selectedMode) {
      case 'auto':
        return <Speed color="primary" />;
      case 'reference':
        return <Engineering color="secondary" />;
      case 'hybrid':
        return <Psychology color="success" />;
      case 'advanced':
        return <Science color="action" />;
      default:
        return <Info />;
    }
  };

  const getModeEstimatedTime = (selectedMode: ProcessingMode): string => {
    switch (selectedMode) {
      case 'auto':
        return '5-15 seconds';
      case 'reference':
        return '30-60 seconds';
      case 'hybrid':
        return '45-90 seconds';
      case 'advanced':
        return '2-5 minutes';
      default:
        return 'Unknown';
    }
  };

  const getModeComplexity = (selectedMode: ProcessingMode): string => {
    switch (selectedMode) {
      case 'auto':
        return 'Beginner';
      case 'reference':
        return 'Intermediate';
      case 'hybrid':
        return 'Intermediate';
      case 'advanced':
        return 'Expert';
      default:
        return 'Unknown';
    }
  };

  const getModeQuality = (selectedMode: ProcessingMode): string => {
    switch (selectedMode) {
      case 'auto':
        return 'Good';
      case 'reference':
        return 'Professional';
      case 'hybrid':
        return 'Excellent';
      case 'advanced':
        return 'Research';
      default:
        return 'Unknown';
    }
  };

  const getModeTargetUsers = (selectedMode: ProcessingMode): string => {
    switch (selectedMode) {
      case 'auto':
        return 'Content creators, podcasters, quick projects';
      case 'reference':
        return 'Audio engineers, professionals, traditional workflow';
      case 'hybrid':
        return 'Professionals, AI-assisted workflow, best of both worlds';
      case 'advanced':
        return 'Researchers, audiophiles, cutting-edge production';
      default:
        return 'General users';
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
            {(['auto', 'reference', 'hybrid', 'advanced'] as const).map((modeOption) => (
              <Chip
                key={modeOption}
                label={getModeDisplayName(modeOption)}
                variant={mode === modeOption ? 'filled' : 'outlined'}
                color={mode === modeOption ? getModeColor(modeOption) : 'default'}
                onClick={() => onModeChange(modeOption)}
                disabled={disabled}
                sx={{ 
                  textTransform: 'capitalize',
                  minWidth: '120px',
                  position: 'relative'
                }}
              />
            ))}
          </Box>
          <Typography variant="caption" color="text.secondary">
            {getModeDescription(mode)}
          </Typography>
          
          {/* Mode Information Panel */}
          <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              {getModeIcon(mode)}
              <Typography variant="subtitle2" color="text.primary">
                {getModeDisplayName(mode)} Details
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 1 }}>
              <Chip 
                size="small" 
                label={`${getModeEstimatedTime(mode)}`} 
                variant="outlined" 
                color="primary" 
              />
              <Chip 
                size="small" 
                label={`${getModeComplexity(mode)} level`} 
                variant="outlined" 
                color="secondary" 
              />
              <Chip 
                size="small" 
                label={`${getModeQuality(mode)} quality`} 
                variant="outlined" 
                color="success" 
              />
            </Box>
            
            <Typography variant="caption" color="text.secondary">
              Best for: {getModeTargetUsers(mode)}
            </Typography>
          </Box>
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