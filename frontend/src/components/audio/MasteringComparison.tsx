import { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Chip,
  Divider,
  Alert,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  CompareArrows,
  Download,
  VolumeUp,
  VolumeOff,
  Equalizer,
  TrendingUp,
  Assessment,
} from '@mui/icons-material';
import WaveformVisualizationV2 from './WaveformVisualizationV2';

interface AudioMetrics {
  rms: number;
  peak: number;
  lufs: number;
  truePeak: number;
  dynamicRange: number;
  stereoWidth: number;
  spectralCentroid: number;
  fileSize: number;
  duration: number;
}

interface ProcessingResult {
  jobId: string;
  originalFile: {
    name: string;
    url: string;
    metrics: AudioMetrics;
  };
  processedFile: {
    name: string;
    url: string;
    metrics: AudioMetrics;
  };
  processingSettings: {
    mode: string;
    intensity: string;
    eqStyle: string;
    targetLoudness: number;
    preserveDynamics: boolean;
  };
  aiPredictions?: {
    modelUsed: string;
    confidence: number;
    predictedGenre: string;
    audioCharacteristics: any;
  };
  processingTime: number;
}

interface MasteringComparisonProps {
  processingResult: ProcessingResult;
  onDownload?: (fileType: 'original' | 'processed') => void;
  onNewProcessing?: () => void;
}

const MasteringComparison = ({
  processingResult,
  onDownload,
  onNewProcessing,
}: MasteringComparisonProps): JSX.Element => {
  const [activePlayer, setActivePlayer] = useState<'original' | 'processed' | null>(null);
  const [comparisonMode, setComparisonMode] = useState<'side-by-side' | 'a-b' | 'overlay'>('side-by-side');
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const handlePlayPause = useCallback((player: 'original' | 'processed') => {
    if (activePlayer === player) {
      setActivePlayer(null);
    } else {
      setActivePlayer(player);
    }
  }, [activePlayer]);

  const calculateImprovement = useCallback((original: number, processed: number, higherIsBetter: boolean = true): number => {
    if (original === 0) return 0;
    const change = ((processed - original) / Math.abs(original)) * 100;
    return higherIsBetter ? change : -change;
  }, []);

  const formatMetricValue = useCallback((value: number, unit: string, decimals: number = 2): string => {
    return `${value.toFixed(decimals)} ${unit}`;
  }, []);

  const getImprovementColor = useCallback((improvement: number): 'success' | 'warning' | 'error' => {
    if (improvement > 5) return 'success';
    if (improvement > -5) return 'warning';
    return 'error';
  }, []);

  const getImprovementIcon = useCallback((improvement: number) => {
    if (improvement > 5) return <TrendingUp color="success" />;
    if (improvement > -5) return <Assessment color="warning" />;
    return <TrendingUp color="error" sx={{ transform: 'rotate(180deg)' }} />;
  }, []);

  const metricsComparison = [
    {
      name: 'Loudness (LUFS)',
      original: processingResult.originalFile.metrics.lufs,
      processed: processingResult.processedFile.metrics.lufs,
      unit: 'LUFS',
      higherIsBetter: true,
      description: 'Perceived loudness standard for broadcasting',
    },
    {
      name: 'Peak Level',
      original: processingResult.originalFile.metrics.peak,
      processed: processingResult.processedFile.metrics.peak,
      unit: 'dB',
      higherIsBetter: false,
      description: 'Maximum amplitude to prevent clipping',
    },
    {
      name: 'Dynamic Range',
      original: processingResult.originalFile.metrics.dynamicRange,
      processed: processingResult.processedFile.metrics.dynamicRange,
      unit: 'dB',
      higherIsBetter: true,
      description: 'Difference between loudest and quietest parts',
    },
    {
      name: 'RMS Level',
      original: processingResult.originalFile.metrics.rms,
      processed: processingResult.processedFile.metrics.rms,
      unit: 'dB',
      higherIsBetter: true,
      description: 'Average signal power',
    },
    {
      name: 'Stereo Width',
      original: processingResult.originalFile.metrics.stereoWidth,
      processed: processingResult.processedFile.metrics.stereoWidth,
      unit: '%',
      higherIsBetter: true,
      description: 'Stereo field width and imaging',
    },
    {
      name: 'Spectral Centroid',
      original: processingResult.originalFile.metrics.spectralCentroid,
      processed: processingResult.processedFile.metrics.spectralCentroid,
      unit: 'Hz',
      higherIsBetter: false,
      description: 'Brightness indicator of the sound',
    },
  ];

  return (
    <Box sx={{ mt: 3 }}>
      <Card elevation={3}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" component="h2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Equalizer color="primary" />
              Mastering Results Comparison
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                onClick={() => setComparisonMode(comparisonMode === 'side-by-side' ? 'a-b' : 'side-by-side')}
                startIcon={<CompareArrows />}
              >
                {comparisonMode === 'side-by-side' ? 'A/B Compare' : 'Side by Side'}
              </Button>
              <Button
                variant="contained"
                onClick={onNewProcessing}
                color="primary"
              >
                Process Another Track
              </Button>
            </Box>
          </Box>

          {/* Processing Summary */}
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="body1">
              <strong>Processing Completed Successfully!</strong>
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Your track has been mastered using <strong>{processingResult.processingSettings.mode}</strong> mode
              with <strong>{processingResult.processingSettings.intensity}</strong> intensity.
              {processingResult.aiPredictions && (
                <>
                  {' '}AI detected genre: <strong>{processingResult.aiPredictions.predictedGenre}</strong> 
                  (confidence: {(processingResult.aiPredictions.confidence * 100).toFixed(1)}%)
                </>
              )}
            </Typography>
          </Alert>

          {/* Audio Player Comparison */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" color="text.secondary">
                      Original Audio
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Tooltip title="Download Original">
                        <IconButton onClick={() => onDownload?.('original')} size="small">
                          <Download />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={activePlayer === 'original' ? 'Pause' : 'Play'}>
                        <IconButton
                          onClick={() => handlePlayPause('original')}
                          color={activePlayer === 'original' ? 'primary' : 'default'}
                        >
                          {activePlayer === 'original' ? <Pause /> : <PlayArrow />}
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                  <WaveformVisualizationV2
                    audioUrl={processingResult.originalFile.url}
                    title={processingResult.originalFile.name}
                    height={80}
                    waveColor="#1976d2"
                    progressColor="#bbdefb"
                    disabled={activePlayer !== null && activePlayer !== 'original'}
                    onTimeUpdate={setCurrentTime}
                    onDurationChange={setDuration}
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Duration: {formatMetricValue(processingResult.originalFile.metrics.duration, 's', 1)} | 
                    Size: {formatMetricValue(processingResult.originalFile.metrics.fileSize / 1024 / 1024, 'MB', 1)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ borderColor: 'success.main', borderWidth: 2 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" color="success.main">
                      Mastered Audio
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Chip
                        label="NEW"
                        color="success"
                        size="small"
                      />
                      <Tooltip title="Download Mastered">
                        <IconButton onClick={() => onDownload?.('processed')} size="small" color="success">
                          <Download />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={activePlayer === 'processed' ? 'Pause' : 'Play'}>
                        <IconButton
                          onClick={() => handlePlayPause('processed')}
                          color={activePlayer === 'processed' ? 'success' : 'default'}
                        >
                          {activePlayer === 'processed' ? <Pause /> : <PlayArrow />}
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                  <WaveformVisualizationV2
                    audioUrl={processingResult.processedFile.url}
                    title={processingResult.processedFile.name}
                    height={80}
                    waveColor="#4caf50"
                    progressColor="#c8e6c9"
                    disabled={activePlayer !== null && activePlayer !== 'processed'}
                    onTimeUpdate={setCurrentTime}
                    onDurationChange={setDuration}
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Duration: {formatMetricValue(processingResult.processedFile.metrics.duration, 's', 1)} | 
                    Size: {formatMetricValue(processingResult.processedFile.metrics.fileSize / 1024 / 1024, 'MB', 1)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Technical Metrics Comparison */}
          {showTechnicalDetails && (
            <>
              <Divider sx={{ my: 3 }} />
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Assessment color="primary" />
                Technical Analysis & Improvements
              </Typography>

              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Metric</strong></TableCell>
                      <TableCell align="right"><strong>Original</strong></TableCell>
                      <TableCell align="right"><strong>Mastered</strong></TableCell>
                      <TableCell align="right"><strong>Improvement</strong></TableCell>
                      <TableCell><strong>Description</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {metricsComparison.map((metric) => {
                      const improvement = calculateImprovement(metric.original, metric.processed, metric.higherIsBetter);
                      return (
                        <TableRow key={metric.name}>
                          <TableCell component="th" scope="row">
                            <strong>{metric.name}</strong>
                          </TableCell>
                          <TableCell align="right">
                            {formatMetricValue(metric.original, metric.unit)}
                          </TableCell>
                          <TableCell align="right">
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                              {formatMetricValue(metric.processed, metric.unit)}
                              {getImprovementIcon(improvement)}
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${improvement > 0 ? '+' : ''}${improvement.toFixed(1)}%`}
                              color={getImprovementColor(improvement)}
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption" color="text.secondary">
                              {metric.description}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}

          {/* Processing Information */}
          <Divider sx={{ my: 3 }} />
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Processing Settings
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Chip label={`Mode: ${processingResult.processingSettings.mode}`} variant="outlined" size="small" />
                <Chip label={`Intensity: ${processingResult.processingSettings.intensity}`} variant="outlined" size="small" />
                <Chip label={`EQ Style: ${processingResult.processingSettings.eqStyle}`} variant="outlined" size="small" />
                <Chip label={`Target: ${processingResult.processingSettings.targetLoudness} LUFS`} variant="outlined" size="small" />
                <Chip 
                  label={`Dynamics: ${processingResult.processingSettings.preserveDynamics ? 'Preserved' : 'Enhanced'}`} 
                  variant="outlined" 
                  size="small" 
                />
              </Box>
            </Grid>
            
            {processingResult.aiPredictions && (
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  AI Analysis
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Chip label={`Model: ${processingResult.aiPredictions.modelUsed}`} variant="outlined" size="small" />
                  <Chip label={`Genre: ${processingResult.aiPredictions.predictedGenre}`} variant="outlined" size="small" />
                  <Chip 
                    label={`Confidence: ${(processingResult.aiPredictions.confidence * 100).toFixed(1)}%`} 
                    variant="outlined" 
                    size="small" 
                  />
                  <Chip 
                    label={`Processing Time: ${processingResult.processingTime.toFixed(1)}s`} 
                    variant="outlined" 
                    size="small" 
                  />
                </Box>
              </Grid>
            )}
          </Grid>

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 3 }}>
            <Button
              variant="contained"
              onClick={() => onDownload?.('processed')}
              startIcon={<Download />}
              color="success"
              size="large"
            >
              Download Mastered Track
            </Button>
            <Button
              variant="outlined"
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              startIcon={<Assessment />}
            >
              {showTechnicalDetails ? 'Hide' : 'Show'} Technical Details
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default MasteringComparison;