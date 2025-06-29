import { useEffect, useRef, useState, useCallback } from 'react';
import { Box, Typography, Card, CardContent, Chip, LinearProgress } from '@mui/material';
import { styled } from '@mui/material/styles';

interface AudioAnalyzerProps {
  readonly audioElement: HTMLAudioElement | null;
  readonly isPlaying: boolean;
  readonly onAnalysisUpdate?: (analysis: AudioAnalysis) => void;
}

interface AudioAnalysis {
  readonly frequencyData: Uint8Array;
  readonly timeDomainData: Uint8Array;
  readonly rms: number;
  readonly peak: number;
  readonly centroid: number;
  readonly rolloff: number;
}

interface FrequencyBand {
  readonly name: string;
  readonly min: number;
  readonly max: number;
  readonly color: string;
}

const AnalyzerCanvas = styled('canvas')(({ theme }) => ({
  width: '100%',
  height: '200px',
  backgroundColor: 'rgba(0, 0, 0, 0.3)',
  borderRadius: theme.shape.borderRadius,
  border: '1px solid rgba(255, 255, 255, 0.1)',
}));

const MeterContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(1),
  padding: theme.spacing(2),
  backgroundColor: 'rgba(0, 0, 0, 0.2)',
  borderRadius: theme.shape.borderRadius,
  border: '1px solid rgba(255, 255, 255, 0.1)',
}));

const AudioAnalyzer = ({ audioElement, isPlaying, onAnalysisUpdate }: AudioAnalyzerProps): JSX.Element => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  
  const [analysis, setAnalysis] = useState<AudioAnalysis | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  const frequencyBands: readonly FrequencyBand[] = [
    { name: 'Sub Bass', min: 20, max: 60, color: '#ff6b6b' },
    { name: 'Bass', min: 60, max: 250, color: '#ff8e8e' },
    { name: 'Low Mid', min: 250, max: 500, color: '#ffa726' },
    { name: 'Mid', min: 500, max: 2000, color: '#fed535' },
    { name: 'High Mid', min: 2000, max: 4000, color: '#66bb6a' },
    { name: 'Presence', min: 4000, max: 8000, color: '#42a5f5' },
    { name: 'Brilliance', min: 8000, max: 20000, color: '#ab47bc' },
  ];

  const initializeAudioContext = useCallback(async (): Promise<void> => {
    if (!audioElement || isInitialized) return;

    try {
      // Create audio context
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // Create analyzer node
      analyzerRef.current = audioContextRef.current.createAnalyser();
      analyzerRef.current.fftSize = 2048;
      analyzerRef.current.smoothingTimeConstant = 0.8;
      
      // Create source from audio element
      sourceRef.current = audioContextRef.current.createMediaElementSource(audioElement);
      
      // Connect: source -> analyzer -> destination
      sourceRef.current.connect(analyzerRef.current);
      analyzerRef.current.connect(audioContextRef.current.destination);
      
      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to initialize audio context:', error);
    }
  }, [audioElement, isInitialized]);

  const calculateAudioFeatures = useCallback((frequencyData: Uint8Array, timeDomainData: Uint8Array): AudioAnalysis => {
    // RMS (Root Mean Square) for loudness
    let rmsSum = 0;
    for (let i = 0; i < timeDomainData.length; i++) {
      const sample = (timeDomainData[i] - 128) / 128;
      rmsSum += sample * sample;
    }
    const rms = Math.sqrt(rmsSum / timeDomainData.length);

    // Peak amplitude
    let peak = 0;
    for (let i = 0; i < timeDomainData.length; i++) {
      const sample = Math.abs((timeDomainData[i] - 128) / 128);
      if (sample > peak) peak = sample;
    }

    // Spectral centroid (brightness)
    let weightedSum = 0;
    let magnitudeSum = 0;
    for (let i = 1; i < frequencyData.length; i++) {
      const magnitude = frequencyData[i] / 255;
      weightedSum += i * magnitude;
      magnitudeSum += magnitude;
    }
    const centroid = magnitudeSum > 0 ? weightedSum / magnitudeSum : 0;

    // Spectral rolloff (90% of energy)
    let cumulativeEnergy = 0;
    const totalEnergy = frequencyData.reduce((sum, val) => sum + (val / 255) ** 2, 0);
    const rolloffThreshold = totalEnergy * 0.9;
    let rolloff = 0;
    
    for (let i = 0; i < frequencyData.length; i++) {
      cumulativeEnergy += (frequencyData[i] / 255) ** 2;
      if (cumulativeEnergy >= rolloffThreshold) {
        rolloff = i;
        break;
      }
    }

    return {
      frequencyData,
      timeDomainData,
      rms,
      peak,
      centroid: centroid / frequencyData.length,
      rolloff: rolloff / frequencyData.length,
    };
  }, []);

  const drawFrequencySpectrum = useCallback((canvas: HTMLCanvasElement, frequencyData: Uint8Array): void => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.fillStyle = 'rgba(10, 11, 13, 0.8)';
    ctx.fillRect(0, 0, width, height);

    // Draw frequency bars
    const barWidth = width / frequencyData.length;
    const barSpacing = barWidth * 0.1;
    const actualBarWidth = barWidth - barSpacing;

    for (let i = 0; i < frequencyData.length; i++) {
      const barHeight = (frequencyData[i] / 255) * height * 0.8;
      const x = i * barWidth;
      const y = height - barHeight;

      // Create gradient for each bar
      const gradient = ctx.createLinearGradient(0, height, 0, y);
      
      // Determine color based on frequency range
      const frequency = (i / frequencyData.length) * 22050; // Nyquist frequency
      let color = '#fed535';
      
      if (frequency < 250) color = '#ff6b6b';
      else if (frequency < 500) color = '#ff8e8e';
      else if (frequency < 2000) color = '#ffa726';
      else if (frequency < 4000) color = '#fed535';
      else if (frequency < 8000) color = '#66bb6a';
      else if (frequency < 16000) color = '#42a5f5';
      else color = '#ab47bc';

      gradient.addColorStop(0, color + '80');
      gradient.addColorStop(1, color);

      ctx.fillStyle = gradient;
      ctx.fillRect(x, y, actualBarWidth, barHeight);
    }

    // Draw frequency labels
    ctx.fillStyle = '#ffffff80';
    ctx.font = '12px Inter';
    ctx.textAlign = 'center';
    
    const labelPositions = [
      { freq: '60Hz', pos: 0.05 },
      { freq: '250Hz', pos: 0.15 },
      { freq: '1kHz', pos: 0.3 },
      { freq: '4kHz', pos: 0.5 },
      { freq: '8kHz', pos: 0.7 },
      { freq: '16kHz', pos: 0.9 },
    ];

    labelPositions.forEach(({ freq, pos }) => {
      ctx.fillText(freq, width * pos, height - 5);
    });
  }, []);

  const animate = useCallback((): void => {
    if (!analyzerRef.current || !canvasRef.current || !isPlaying) return;

    const frequencyData = new Uint8Array(analyzerRef.current.frequencyBinCount);
    const timeDomainData = new Uint8Array(analyzerRef.current.fftSize);
    
    analyzerRef.current.getByteFrequencyData(frequencyData);
    analyzerRef.current.getByteTimeDomainData(timeDomainData);

    // Calculate audio features
    const audioAnalysis = calculateAudioFeatures(frequencyData, timeDomainData);
    setAnalysis(audioAnalysis);
    onAnalysisUpdate?.(audioAnalysis);

    // Draw visualization
    drawFrequencySpectrum(canvasRef.current, frequencyData);

    animationFrameRef.current = requestAnimationFrame(animate);
  }, [isPlaying, calculateAudioFeatures, drawFrequencySpectrum, onAnalysisUpdate]);

  // Initialize audio context when audio element is available
  useEffect(() => {
    if (audioElement && !isInitialized) {
      initializeAudioContext();
    }
  }, [audioElement, isInitialized, initializeAudioContext]);

  // Start/stop animation based on playback state
  useEffect(() => {
    if (isPlaying && isInitialized) {
      // Resume audio context if suspended
      if (audioContextRef.current?.state === 'suspended') {
        audioContextRef.current.resume();
      }
      animate();
    } else if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isPlaying, isInitialized, animate]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Set canvas size
  useEffect(() => {
    if (canvasRef.current) {
      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      canvas.getContext('2d')?.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
  }, []);

  const formatValue = (value: number, decimals: number = 2): string => {
    return value.toFixed(decimals);
  };

  const getLoudnessLevel = (rms: number): { level: string; color: string } => {
    if (rms < 0.1) return { level: 'Quiet', color: '#66bb6a' };
    if (rms < 0.3) return { level: 'Moderate', color: '#fed535' };
    if (rms < 0.7) return { level: 'Loud', color: '#ffa726' };
    return { level: 'Very Loud', color: '#ff6b6b' };
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        Real-Time Audio Analysis
        {isPlaying && isInitialized && (
          <Chip 
            label="LIVE" 
            size="small" 
            sx={{ 
              backgroundColor: '#51cf66',
              color: '#0a0b0d',
              fontWeight: 700,
              animation: 'pulse 2s infinite',
              '@keyframes pulse': {
                '0%': { opacity: 1 },
                '50%': { opacity: 0.7 },
                '100%': { opacity: 1 },
              },
            }} 
          />
        )}
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Frequency Spectrum
          </Typography>
          <AnalyzerCanvas 
            ref={canvasRef}
            style={{ display: 'block' }}
          />
        </CardContent>
      </Card>

      {analysis && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
          <MeterContainer>
            <Typography variant="subtitle2" gutterBottom>
              Loudness Meter
            </Typography>
            <Box sx={{ mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                RMS: {formatValue(analysis.rms * 100)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={analysis.rms * 100}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: getLoudnessLevel(analysis.rms).color,
                  },
                }}
              />
            </Box>
            <Box sx={{ mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Peak: {formatValue(analysis.peak * 100)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={analysis.peak * 100}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: analysis.peak > 0.9 ? '#ff6b6b' : '#fed535',
                  },
                }}
              />
            </Box>
            <Chip 
              label={getLoudnessLevel(analysis.rms).level}
              size="small"
              sx={{ 
                backgroundColor: getLoudnessLevel(analysis.rms).color + '20',
                color: getLoudnessLevel(analysis.rms).color,
                fontWeight: 600,
              }}
            />
          </MeterContainer>

          <MeterContainer>
            <Typography variant="subtitle2" gutterBottom>
              Spectral Features
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Brightness
                </Typography>
                <Typography variant="body2">
                  {formatValue(analysis.centroid * 100)}%
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Rolloff
                </Typography>
                <Typography variant="body2">
                  {formatValue(analysis.rolloff * 100)}%
                </Typography>
              </Box>
              <Chip 
                label={analysis.centroid > 0.5 ? 'Bright' : 'Warm'}
                size="small"
                sx={{ 
                  backgroundColor: analysis.centroid > 0.5 ? '#42a5f520' : '#ffa72620',
                  color: analysis.centroid > 0.5 ? '#42a5f5' : '#ffa726',
                  fontWeight: 600,
                  alignSelf: 'flex-start',
                }}
              />
            </Box>
          </MeterContainer>
        </Box>
      )}

      {!isInitialized && audioElement && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            Click play to start audio analysis
          </Typography>
        </Box>
      )}

      {!audioElement && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            Upload an audio file to see real-time analysis
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default AudioAnalyzer;