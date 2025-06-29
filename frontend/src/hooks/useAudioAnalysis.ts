import { useState, useCallback, useRef, useEffect } from 'react';

export interface AudioAnalysisData {
  readonly frequencyData: Uint8Array;
  readonly timeDomainData: Uint8Array;
  readonly rms: number;
  readonly peak: number;
  readonly centroid: number;
  readonly rolloff: number;
  readonly averageFrequency: number;
  readonly dynamicRange: number;
}

export interface AudioAnalysisConfig {
  readonly fftSize?: number;
  readonly smoothingTimeConstant?: number;
  readonly updateInterval?: number;
}

export interface UseAudioAnalysisReturn {
  readonly analysisData: AudioAnalysisData | null;
  readonly isAnalyzing: boolean;
  readonly error: string | null;
  readonly initializeAnalysis: (audioElement: HTMLAudioElement) => Promise<void>;
  readonly startAnalysis: () => void;
  readonly stopAnalysis: () => void;
  readonly resetAnalysis: () => void;
}

const defaultConfig: Required<AudioAnalysisConfig> = {
  fftSize: 2048,
  smoothingTimeConstant: 0.8,
  updateInterval: 50, // ms
};

export const useAudioAnalysis = (config: AudioAnalysisConfig = {}): UseAudioAnalysisReturn => {
  const [analysisData, setAnalysisData] = useState<AudioAnalysisData | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const configRef = useRef({ ...defaultConfig, ...config });

  const calculateAudioFeatures = useCallback((
    frequencyData: Uint8Array,
    timeDomainData: Uint8Array
  ): AudioAnalysisData => {
    // RMS (Root Mean Square) for loudness
    let rmsSum = 0;
    for (let i = 0; i < timeDomainData.length; i++) {
      const sample = (timeDomainData[i] - 128) / 128;
      rmsSum += sample * sample;
    }
    const rms = Math.sqrt(rmsSum / timeDomainData.length);

    // Peak amplitude
    let peak = 0;
    let minPeak = 1;
    for (let i = 0; i < timeDomainData.length; i++) {
      const sample = Math.abs((timeDomainData[i] - 128) / 128);
      if (sample > peak) peak = sample;
      if (sample < minPeak) minPeak = sample;
    }

    // Dynamic range
    const dynamicRange = peak - minPeak;

    // Spectral centroid (brightness)
    let weightedSum = 0;
    let magnitudeSum = 0;
    for (let i = 1; i < frequencyData.length; i++) {
      const magnitude = frequencyData[i] / 255;
      weightedSum += i * magnitude;
      magnitudeSum += magnitude;
    }
    const centroid = magnitudeSum > 0 ? weightedSum / magnitudeSum : 0;

    // Average frequency content
    const averageFrequency = frequencyData.reduce((sum, val) => sum + val, 0) / frequencyData.length;

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
      frequencyData: frequencyData.slice(), // Create a copy
      timeDomainData: timeDomainData.slice(), // Create a copy
      rms,
      peak,
      centroid: centroid / frequencyData.length,
      rolloff: rolloff / frequencyData.length,
      averageFrequency: averageFrequency / 255,
      dynamicRange,
    };
  }, []);

  const initializeAnalysis = useCallback(async (audioElement: HTMLAudioElement): Promise<void> => {
    try {
      setError(null);

      // Clean up existing context
      if (audioContextRef.current) {
        await audioContextRef.current.close();
      }

      // Create new audio context
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // Create analyzer node
      analyzerRef.current = audioContextRef.current.createAnalyser();
      analyzerRef.current.fftSize = configRef.current.fftSize;
      analyzerRef.current.smoothingTimeConstant = configRef.current.smoothingTimeConstant;
      
      // Create source from audio element (only if not already created)
      if (!sourceRef.current) {
        sourceRef.current = audioContextRef.current.createMediaElementSource(audioElement);
      }
      
      // Connect: source -> analyzer -> destination
      sourceRef.current.connect(analyzerRef.current);
      analyzerRef.current.connect(audioContextRef.current.destination);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to initialize audio analysis';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const updateAnalysis = useCallback((): void => {
    if (!analyzerRef.current) return;

    try {
      const frequencyData = new Uint8Array(analyzerRef.current.frequencyBinCount);
      const timeDomainData = new Uint8Array(analyzerRef.current.fftSize);
      
      analyzerRef.current.getByteFrequencyData(frequencyData);
      analyzerRef.current.getByteTimeDomainData(timeDomainData);

      const analysis = calculateAudioFeatures(frequencyData, timeDomainData);
      setAnalysisData(analysis);
    } catch (err) {
      console.error('Error updating analysis:', err);
      setError('Failed to update audio analysis');
    }
  }, [calculateAudioFeatures]);

  const startAnalysis = useCallback((): void => {
    if (!analyzerRef.current || isAnalyzing) return;

    try {
      // Resume audio context if suspended
      if (audioContextRef.current?.state === 'suspended') {
        audioContextRef.current.resume();
      }

      setIsAnalyzing(true);
      setError(null);

      // Start regular updates
      intervalRef.current = setInterval(updateAnalysis, configRef.current.updateInterval);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start audio analysis';
      setError(errorMessage);
      setIsAnalyzing(false);
    }
  }, [isAnalyzing, updateAnalysis]);

  const stopAnalysis = useCallback((): void => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsAnalyzing(false);
  }, []);

  const resetAnalysis = useCallback((): void => {
    stopAnalysis();
    setAnalysisData(null);
    setError(null);
  }, [stopAnalysis]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  return {
    analysisData,
    isAnalyzing,
    error,
    initializeAnalysis,
    startAnalysis,
    stopAnalysis,
    resetAnalysis,
  };
};