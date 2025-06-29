import { useState, useCallback, useRef, useEffect } from 'react';
import type { AudioFileMetadata } from '@/types';

interface AudioTrack {
  readonly id: string;
  readonly name: string;
  readonly url: string;
  readonly metadata: AudioFileMetadata;
  readonly audioBuffer?: ArrayBuffer;
}

interface PlaybackState {
  readonly currentTrack: AudioTrack | null;
  readonly isPlaying: boolean;
  readonly currentTime: number;
  readonly duration: number;
  readonly volume: number;
  readonly isLoading: boolean;
  readonly error: string | null;
}

interface UseAudioPlaybackOptions {
  readonly autoPlay?: boolean;
  readonly loop?: boolean;
  readonly volume?: number;
  readonly onTrackEnd?: (track: AudioTrack) => void;
  readonly onTimeUpdate?: (currentTime: number, track: AudioTrack) => void;
}

interface UseAudioPlaybackReturn {
  readonly playbackState: PlaybackState;
  readonly loadTrack: (track: AudioTrack) => Promise<void>;
  readonly play: () => Promise<void>;
  readonly pause: () => void;
  readonly stop: () => void;
  readonly seekTo: (time: number) => void;
  readonly setVolume: (volume: number) => void;
  readonly clearTrack: () => void;
  readonly togglePlayPause: () => Promise<void>;
}

const useAudioPlayback = (options: UseAudioPlaybackOptions = {}): UseAudioPlaybackReturn => {
  const {
    autoPlay = false,
    loop = false,
    volume: initialVolume = 0.5,
    onTrackEnd,
    onTimeUpdate,
  } = options;

  const audioContextRef = useRef<AudioContext | null>(null);
  const audioBufferRef = useRef<AudioBuffer | null>(null);
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const startTimeRef = useRef<number>(0);
  const pauseTimeRef = useRef<number>(0);
  const animationFrameRef = useRef<number | null>(null);

  const [state, setState] = useState<PlaybackState>({
    currentTrack: null,
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    volume: initialVolume,
    isLoading: false,
    error: null,
  });

  // Initialize AudioContext
  const initializeAudioContext = useCallback(async (): Promise<AudioContext> => {
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      return audioContextRef.current;
    }

    const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const audioContext = new AudioContextClass();
    
    if (audioContext.state === 'suspended') {
      await audioContext.resume();
    }

    audioContextRef.current = audioContext;
    return audioContext;
  }, []);

  // Update current time animation
  const updateCurrentTime = useCallback((): void => {
    if (!audioContextRef.current || !state.isPlaying || !state.currentTrack) {
      return;
    }

    const currentTime = pauseTimeRef.current + (audioContextRef.current.currentTime - startTimeRef.current);
    const clampedTime = Math.min(currentTime, state.duration);

    setState(prev => ({ ...prev, currentTime: clampedTime }));
    onTimeUpdate?.(clampedTime, state.currentTrack);

    if (clampedTime >= state.duration) {
      // Track ended
      setState(prev => ({ ...prev, isPlaying: false, currentTime: 0 }));
      pauseTimeRef.current = 0;
      onTrackEnd?.(state.currentTrack);
      
      if (loop && audioContextRef.current && audioBufferRef.current) {
        // Reset to beginning and restart playback for loop
        pauseTimeRef.current = 0;
        setState(prev => ({ ...prev, currentTime: 0 }));
        
        // Restart playback
        const sourceNode = audioContextRef.current.createBufferSource();
        sourceNode.buffer = audioBufferRef.current;
        if (gainNodeRef.current) {
          sourceNode.connect(gainNodeRef.current);
        }
        sourceNodeRef.current = sourceNode;
        sourceNode.start(0, 0);
        startTimeRef.current = audioContextRef.current.currentTime;
        setState(prev => ({ ...prev, isPlaying: true }));
        animationFrameRef.current = requestAnimationFrame(updateCurrentTime);
      }
    } else {
      animationFrameRef.current = requestAnimationFrame(updateCurrentTime);
    }
  }, [state.isPlaying, state.duration, state.currentTrack, onTimeUpdate, onTrackEnd, loop]);

  // Load audio track
  const loadTrack = useCallback(async (track: AudioTrack): Promise<void> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const audioContext = await initializeAudioContext();

      // Load audio data
      let audioData: ArrayBuffer;
      
      if (track.audioBuffer) {
        audioData = track.audioBuffer;
      } else {
        const response = await fetch(track.url);
        if (!response.ok) {
          throw new Error(`Failed to load audio: ${response.statusText}`);
        }
        audioData = await response.arrayBuffer();
      }

      // Decode audio data
      const audioBuffer = await audioContext.decodeAudioData(audioData);
      audioBufferRef.current = audioBuffer;

      // Create gain node for volume control
      const gainNode = audioContext.createGain();
      gainNode.gain.value = state.volume;
      gainNode.connect(audioContext.destination);
      gainNodeRef.current = gainNode;

      setState(prev => ({
        ...prev,
        currentTrack: track,
        duration: audioBuffer.duration,
        currentTime: 0,
        isLoading: false,
        error: null,
      }));

      pauseTimeRef.current = 0;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load audio track';
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, [initializeAudioContext, state.volume]);

  // Play audio
  const play = useCallback(async (): Promise<void> => {
    if (!audioContextRef.current || !audioBufferRef.current || !gainNodeRef.current || state.isPlaying) {
      return;
    }

    try {
      // Resume AudioContext if suspended
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume();
      }

      // Create and configure source node
      const sourceNode = audioContextRef.current.createBufferSource();
      sourceNode.buffer = audioBufferRef.current;
      sourceNode.connect(gainNodeRef.current);
      sourceNodeRef.current = sourceNode;

      // Start playback from current position
      const startOffset = pauseTimeRef.current;
      sourceNode.start(0, startOffset);
      startTimeRef.current = audioContextRef.current.currentTime;

      setState(prev => ({ ...prev, isPlaying: true }));

      // Start time update animation
      animationFrameRef.current = requestAnimationFrame(updateCurrentTime);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to play audio';
      setState(prev => ({ ...prev, error: errorMessage }));
      throw error;
    }
  }, [state.isPlaying, updateCurrentTime]);

  // Handle autoPlay
  useEffect(() => {
    if (autoPlay && state.currentTrack && !state.isLoading && !state.isPlaying) {
      play().catch(console.error);
    }
  }, [autoPlay, state.currentTrack, state.isLoading, state.isPlaying, play]);

  // Pause audio
  const pause = useCallback((): void => {
    if (!sourceNodeRef.current || !state.isPlaying) {
      return;
    }

    sourceNodeRef.current.stop();
    sourceNodeRef.current = null;

    // Update pause time
    if (audioContextRef.current) {
      pauseTimeRef.current += audioContextRef.current.currentTime - startTimeRef.current;
    }

    setState(prev => ({ ...prev, isPlaying: false }));

    // Cancel animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  }, [state.isPlaying]);

  // Stop audio
  const stop = useCallback((): void => {
    if (sourceNodeRef.current) {
      sourceNodeRef.current.stop();
      sourceNodeRef.current = null;
    }

    pauseTimeRef.current = 0;
    setState(prev => ({ ...prev, isPlaying: false, currentTime: 0 }));

    // Cancel animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  }, []);

  // Seek to specific time
  const seekTo = useCallback((time: number): void => {
    const clampedTime = Math.max(0, Math.min(time, state.duration));
    pauseTimeRef.current = clampedTime;
    
    setState(prev => ({ ...prev, currentTime: clampedTime }));

    // If playing, restart from new position
    if (state.isPlaying && audioContextRef.current && audioBufferRef.current && gainNodeRef.current) {
      // Stop current playback
      if (sourceNodeRef.current) {
        sourceNodeRef.current.stop();
        sourceNodeRef.current = null;
      }
      
      // Start from new position
      const sourceNode = audioContextRef.current.createBufferSource();
      sourceNode.buffer = audioBufferRef.current;
      sourceNode.connect(gainNodeRef.current);
      sourceNodeRef.current = sourceNode;
      sourceNode.start(0, clampedTime);
      startTimeRef.current = audioContextRef.current.currentTime;
      
      // Reset pause time to account for seek
      pauseTimeRef.current = clampedTime;
    }
  }, [state.duration, state.isPlaying]);

  // Set volume
  const setVolume = useCallback((volume: number): void => {
    const clampedVolume = Math.max(0, Math.min(1, volume));
    
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = clampedVolume;
    }
    
    setState(prev => ({ ...prev, volume: clampedVolume }));
  }, []);

  // Clear current track
  const clearTrack = useCallback((): void => {
    stop();
    audioBufferRef.current = null;
    setState(prev => ({
      ...prev,
      currentTrack: null,
      duration: 0,
      currentTime: 0,
      error: null,
    }));
  }, [stop]);

  // Toggle play/pause
  const togglePlayPause = useCallback(async (): Promise<void> => {
    if (state.isPlaying) {
      pause();
    } else {
      await play();
    }
  }, [state.isPlaying, pause, play]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (sourceNodeRef.current) {
        sourceNodeRef.current.stop();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  return {
    playbackState: state,
    loadTrack,
    play,
    pause,
    stop,
    seekTo,
    setVolume,
    clearTrack,
    togglePlayPause,
  };
};

export default useAudioPlayback;