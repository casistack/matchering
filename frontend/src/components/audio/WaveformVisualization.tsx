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

    // Cleanup any existing instance first
    if (wavesurferRef.current) {
      console.log('WaveformVisualization: Destroying existing WaveSurfer instance');
      try {
        wavesurferRef.current.destroy();
      } catch (error) {
        console.warn('WaveformVisualization: Error destroying previous instance:', error);
      }
      wavesurferRef.current = null;
    }

    try {
      console.log('WaveformVisualization: Creating new WaveSurfer instance with URL:', audioUrl);
      
      // WaveSurfer.js v7 API - proper configuration
      const wavesurfer = WaveSurfer.create({
        container: waveformRef.current,
        height,
        waveColor,
        progressColor,
        // V7 uses HTML audio by default - no backend option needed
        barWidth: 2,
        barRadius: 1,
        // Don't load URL in constructor to avoid multiple loads
      });

      wavesurferRef.current = wavesurfer;

      // Event listeners
      wavesurfer.on('ready', () => {
        console.log('WaveformVisualization: Audio ready, duration:', wavesurfer.getDuration());
        setState(prev => ({
          ...prev,
          isLoading: false,
          duration: wavesurfer.getDuration(),
          error: null,
        }));
        onDurationChange?.(wavesurfer.getDuration());
        
        // In WaveSurfer.js v7, access to audio element may be different
        // Try to get the media element using the v7 API
        try {
          const audioElement = wavesurfer.getMediaElement?.() as HTMLAudioElement;
          console.log('WaveformVisualization: Audio element from WaveSurfer v7:', audioElement);
          console.log('WaveformVisualization: Audio element type:', audioElement?.constructor.name);
          
          if (audioElement && audioElement instanceof HTMLAudioElement) {
            console.log('WaveformVisualization: Providing audio element to analyzer');
            onAudioElementReady?.(audioElement);
          } else {
            console.warn('WaveformVisualization: getMediaElement not available or invalid in v7');
            // For v7, we might need a different approach to get audio element
          }
        } catch (error) {
          console.error('WaveformVisualization: Error accessing audio element:', error);
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
        console.error('WaveformVisualization: WaveSurfer error:', error);
        // Handle AbortError specifically
        if (error.name === 'AbortError') {
          console.log('WaveformVisualization: Audio loading was aborted, possibly due to component update');
          return; // Don't set error state for abort errors
        }
        
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error.message || 'Failed to load audio',
        }));
      });

      return () => {
        console.log('WaveformVisualization: Cleanup - destroying WaveSurfer instance');
        try {
          wavesurfer.destroy();
        } catch (error) {
          console.warn('WaveformVisualization: Error during cleanup:', error);
        }
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
    if (!wavesurferRef.current || disabled || !audioUrl) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    const loadAudio = async () => {
      try {
        console.log('WaveformVisualization: Loading audio URL:', audioUrl);
        
        // Load URL using v7 API
        await wavesurferRef.current!.load(audioUrl);
        
      } catch (error) {
        console.error('WaveformVisualization: Audio loading failed:', error);
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Failed to load audio',
        }));
      }
    };

    loadAudio();
  }, [audioUrl, disabled]);

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