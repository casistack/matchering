import { useEffect, useRef, useState, useCallback } from 'react';
import WaveSurfer from 'wavesurfer.js';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Slider,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  VolumeUp,
  ZoomIn,
  ZoomOut,
} from '@mui/icons-material';

interface WaveformVisualizationProps {
  readonly audioUrl?: string;
  readonly audioBuffer?: ArrayBuffer;
  readonly title?: string;
  readonly height?: number;
  readonly waveColor?: string;
  readonly progressColor?: string;
  readonly onTimeUpdate?: (currentTime: number) => void;
  readonly onDurationChange?: (duration: number) => void;
  readonly onAudioElementReady?: (audioElement: HTMLAudioElement) => void;
  readonly disabled?: boolean;
}

interface WaveformState {
  readonly isPlaying: boolean;
  readonly isLoading: boolean;
  readonly currentTime: number;
  readonly duration: number;
  readonly volume: number;
  readonly zoom: number;
  readonly error: string | null;
}

const WaveformVisualization = ({
  audioUrl,
  audioBuffer,
  title = 'Audio Waveform',
  height = 100,
  waveColor = '#fed535',
  progressColor = '#e4e3df',
  onTimeUpdate,
  onDurationChange,
  onAudioElementReady,
  disabled = false,
}: WaveformVisualizationProps): JSX.Element => {
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  
  const [state, setState] = useState<WaveformState>({
    isPlaying: false,
    isLoading: false,
    currentTime: 0,
    duration: 0,
    volume: 0.5,
    zoom: 1,
    error: null,
  });

  // Initialize WaveSurfer
  useEffect(() => {
    if (!waveformRef.current || disabled) return;

    try {
      const wavesurfer = WaveSurfer.create({
        container: waveformRef.current,
        height,
        waveColor,
        progressColor,
        cursorColor: progressColor,
        barWidth: 2,
        barRadius: 1,
        responsive: true,
        normalize: true,
        backend: 'WebAudio',
      });

      wavesurferRef.current = wavesurfer;

      // Event listeners
      wavesurfer.on('ready', () => {
        setState(prev => ({
          ...prev,
          isLoading: false,
          duration: wavesurfer.getDuration(),
          error: null,
        }));
        onDurationChange?.(wavesurfer.getDuration());
        
        // Provide access to audio element for analysis
        const audioElement = wavesurfer.getMediaElement() as HTMLAudioElement;
        if (audioElement) {
          onAudioElementReady?.(audioElement);
        }
      });

      wavesurfer.on('play', () => {
        setState(prev => ({ ...prev, isPlaying: true }));
      });

      wavesurfer.on('pause', () => {
        setState(prev => ({ ...prev, isPlaying: false }));
      });

      wavesurfer.on('finish', () => {
        setState(prev => ({ ...prev, isPlaying: false, currentTime: 0 }));
      });

      wavesurfer.on('audioprocess', (currentTime: number) => {
        setState(prev => ({ ...prev, currentTime }));
        onTimeUpdate?.(currentTime);
      });

      wavesurfer.on('seek', (progress: number) => {
        const currentTime = progress * wavesurfer.getDuration();
        setState(prev => ({ ...prev, currentTime }));
        onTimeUpdate?.(currentTime);
      });

      wavesurfer.on('error', (error: Error) => {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error.message || 'Failed to load audio',
        }));
      });

      return () => {
        wavesurfer.destroy();
      };
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to initialize waveform',
      }));
    }
  }, [height, waveColor, progressColor, onTimeUpdate, onDurationChange, disabled]);

  // Load audio data
  useEffect(() => {
    if (!wavesurferRef.current || disabled) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      if (audioUrl) {
        wavesurferRef.current.load(audioUrl);
      } else if (audioBuffer) {
        wavesurferRef.current.loadArrayBuffer(audioBuffer);
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to load audio',
      }));
    }
  }, [audioUrl, audioBuffer, disabled]);

  const handlePlayPause = useCallback((): void => {
    if (!wavesurferRef.current || disabled) return;

    if (state.isPlaying) {
      wavesurferRef.current.pause();
    } else {
      wavesurferRef.current.play();
    }
  }, [state.isPlaying, disabled]);

  const handleStop = useCallback((): void => {
    if (!wavesurferRef.current || disabled) return;

    wavesurferRef.current.stop();
    setState(prev => ({ ...prev, currentTime: 0 }));
  }, [disabled]);

  const handleVolumeChange = useCallback((_: Event, value: number | number[]): void => {
    if (!wavesurferRef.current || disabled) return;

    const volume = Array.isArray(value) ? value[0] : value;
    const normalizedVolume = volume / 100;
    
    wavesurferRef.current.setVolume(normalizedVolume);
    setState(prev => ({ ...prev, volume: normalizedVolume }));
  }, [disabled]);

  const handleZoomChange = useCallback((delta: number): void => {
    if (!wavesurferRef.current || disabled) return;

    const newZoom = Math.max(1, Math.min(10, state.zoom + delta));
    wavesurferRef.current.zoom(newZoom * 10);
    setState(prev => ({ ...prev, zoom: newZoom }));
  }, [state.zoom, disabled]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (state.error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {state.error}
      </Alert>
    );
  }

  return (
    <Card sx={{ width: '100%', opacity: disabled ? 0.5 : 1 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" component="h3">
            {title}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {formatTime(state.currentTime)} / {formatTime(state.duration)}
            </Typography>
          </Box>
        </Box>

        {/* Waveform Container */}
        <Box
          ref={waveformRef}
          sx={{
            width: '100%',
            height: `${height}px`,
            mb: 2,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1,
            backgroundColor: 'background.paper',
            position: 'relative',
            overflow: 'hidden',
          }}
        />

        {state.isLoading && (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Loading audio waveform...
            </Typography>
          </Box>
        )}

        {/* Controls */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Playback Controls */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              onClick={handlePlayPause}
              disabled={disabled || state.isLoading || state.duration === 0}
              color="primary"
            >
              {state.isPlaying ? <Pause /> : <PlayArrow />}
            </IconButton>
            
            <IconButton
              onClick={handleStop}
              disabled={disabled || state.isLoading || state.duration === 0}
              size="small"
            >
              <Stop />
            </IconButton>
          </Box>

          {/* Volume Control */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 120 }}>
            <VolumeUp fontSize="small" />
            <Slider
              value={state.volume * 100}
              onChange={handleVolumeChange}
              min={0}
              max={100}
              size="small"
              disabled={disabled || state.isLoading}
              sx={{ flex: 1 }}
            />
          </Box>

          {/* Zoom Controls */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Zoom Out">
              <IconButton
                onClick={() => handleZoomChange(-1)}
                disabled={disabled || state.zoom <= 1}
                size="small"
              >
                <ZoomOut fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Typography variant="caption" sx={{ minWidth: 24, textAlign: 'center' }}>
              {state.zoom}x
            </Typography>
            
            <Tooltip title="Zoom In">
              <IconButton
                onClick={() => handleZoomChange(1)}
                disabled={disabled || state.zoom >= 10}
                size="small"
              >
                <ZoomIn fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default WaveformVisualization;