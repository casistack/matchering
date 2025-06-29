import { useRef, useEffect, useState, useCallback } from 'react';
import { useWavesurfer } from '@wavesurfer/react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Slider,
  Tooltip,
  Alert,
  CircularProgress,
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
  readonly title?: string;
  readonly height?: number;
  readonly waveColor?: string;
  readonly progressColor?: string;
  readonly onTimeUpdate?: (currentTime: number) => void;
  readonly onDurationChange?: (duration: number) => void;
  readonly onAudioElementReady?: (audioElement: HTMLAudioElement) => void;
  readonly disabled?: boolean;
}

const WaveformVisualizationV2 = ({
  audioUrl,
  title = 'Audio Waveform',
  height = 100,
  waveColor = '#fed535',
  progressColor = '#e4e3df',
  onTimeUpdate,
  onDurationChange,
  onAudioElementReady,
  disabled = false,
}: WaveformVisualizationProps): JSX.Element => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [volume, setVolume] = useState(50);
  const [zoom, setZoom] = useState(1);
  const [error, setError] = useState<string | null>(null);

  // Use the official WaveSurfer React hook
  const { wavesurfer, isReady, isPlaying, currentTime } = useWavesurfer({
    container: containerRef,
    url: audioUrl,
    waveColor,
    progressColor,
    height,
    barWidth: 2,
    barRadius: 1,
    dragToSeek: !disabled,
    interact: !disabled,
  });

  // Handle ready event
  useEffect(() => {
    if (isReady && wavesurfer) {
      console.log('WaveformVisualizationV2: WaveSurfer ready');
      const duration = wavesurfer.getDuration();
      onDurationChange?.(duration);

      // Get audio element for analyzer
      try {
        const audioElement = wavesurfer.getMediaElement() as HTMLAudioElement;
        if (audioElement && audioElement instanceof HTMLAudioElement) {
          console.log('WaveformVisualizationV2: Providing audio element to analyzer');
          onAudioElementReady?.(audioElement);
        }
      } catch (err) {
        console.warn('WaveformVisualizationV2: Could not get audio element:', err);
      }
    }
  }, [isReady, wavesurfer, onDurationChange, onAudioElementReady]);

  // Handle time updates
  useEffect(() => {
    onTimeUpdate?.(currentTime);
  }, [currentTime, onTimeUpdate]);

  // Handle errors
  useEffect(() => {
    if (wavesurfer) {
      const handleError = (err: Error) => {
        // Ignore abort errors from React StrictMode
        if (err.name === 'AbortError' || err.message?.includes('aborted')) {
          console.log('WaveformVisualizationV2: Ignoring AbortError (expected in StrictMode)');
          return;
        }
        console.error('WaveformVisualizationV2: Error:', err);
        setError(err.message || 'Failed to load audio');
      };

      wavesurfer.on('error', handleError);

      return () => {
        wavesurfer.un('error', handleError);
      };
    }
  }, [wavesurfer]);

  // Playback controls
  const handlePlayPause = useCallback(() => {
    if (wavesurfer && isReady) {
      wavesurfer.playPause();
    }
  }, [wavesurfer, isReady]);

  const handleStop = useCallback(() => {
    if (wavesurfer && isReady) {
      wavesurfer.stop();
    }
  }, [wavesurfer, isReady]);

  // Volume control
  const handleVolumeChange = useCallback(
    (_: Event, value: number | number[]) => {
      const newVolume = Array.isArray(value) ? value[0] : value;
      setVolume(newVolume);
      if (wavesurfer) {
        wavesurfer.setVolume(newVolume / 100);
      }
    },
    [wavesurfer]
  );

  // Zoom control
  const handleZoomChange = useCallback(
    (delta: number) => {
      const newZoom = Math.max(1, Math.min(10, zoom + delta));
      setZoom(newZoom);
      if (wavesurfer) {
        wavesurfer.zoom(newZoom * 10);
      }
    },
    [wavesurfer, zoom]
  );

  // Format time display
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
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
              {formatTime(currentTime)} / {formatTime(wavesurfer?.getDuration() || 0)}
            </Typography>
          </Box>
        </Box>

        {/* Waveform Container */}
        <Box
          ref={containerRef}
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

        {!isReady && audioUrl && (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 2, gap: 1 }}>
            <CircularProgress size={20} />
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
              disabled={disabled || !isReady}
              color="primary"
            >
              {isPlaying ? <Pause /> : <PlayArrow />}
            </IconButton>
            
            <IconButton
              onClick={handleStop}
              disabled={disabled || !isReady}
              size="small"
            >
              <Stop />
            </IconButton>
          </Box>

          {/* Volume Control */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 120 }}>
            <VolumeUp fontSize="small" />
            <Slider
              value={volume}
              onChange={handleVolumeChange}
              min={0}
              max={100}
              size="small"
              disabled={disabled || !isReady}
              sx={{ flex: 1 }}
            />
          </Box>

          {/* Zoom Controls */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Zoom Out">
              <IconButton
                onClick={() => handleZoomChange(-1)}
                disabled={disabled || zoom <= 1}
                size="small"
              >
                <ZoomOut fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Typography variant="caption" sx={{ minWidth: 24, textAlign: 'center' }}>
              {zoom}x
            </Typography>
            
            <Tooltip title="Zoom In">
              <IconButton
                onClick={() => handleZoomChange(1)}
                disabled={disabled || zoom >= 10}
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

export default WaveformVisualizationV2;