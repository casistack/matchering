// Strict audio format definitions
export type AudioFormat = 'wav' | 'mp3' | 'flac' | 'aiff';
export type SampleRate = 22050 | 44100 | 48000 | 96000;
export type BitDepth = 16 | 24 | 32;
export type ChannelCount = 1 | 2;

export interface AudioFileMetadata {
  readonly filename: string;
  readonly format: AudioFormat;
  readonly sampleRate: SampleRate;
  readonly bitDepth: BitDepth;
  readonly channels: ChannelCount;
  readonly duration: number; // seconds
  readonly fileSize: number; // bytes
  readonly checksum: string; // SHA-256
}

export interface AudioAnalysisMetrics {
  readonly rms: number;
  readonly peak: number;
  readonly dynamicRange: number;
  readonly spectralCentroid: number;
  readonly zeroCrossingRate: number;
  readonly mfcc: readonly number[];
  readonly lufs: number;
  readonly truePeak: number;
}

export interface AudioProcessingResult {
  readonly success: boolean;
  readonly outputPath: string | null;
  readonly metadata: AudioFileMetadata;
  readonly metrics: AudioAnalysisMetrics;
  readonly processingTime: number; // milliseconds
  readonly errorMessage?: string;
}

// Type-safe audio context
export interface AudioContextConfig {
  readonly sampleRate: SampleRate;
  readonly channelCount: ChannelCount;
  readonly bitDepth: BitDepth;
}

// Audio buffer with strict typing
export interface TypedAudioBuffer {
  readonly data: Float32Array;
  readonly sampleRate: number;
  readonly duration: number;
  readonly channels: number;
}

// Audio analysis result
export interface AudioAnalysisResult {
  readonly frequencyData: Float32Array;
  readonly timeData: Float32Array;
  readonly rms: number;
  readonly peak: number;
  readonly spectralCentroid: number;
}

// Waveform configuration
export interface WaveformConfig {
  readonly container: HTMLElement;
  readonly waveColor: string;
  readonly progressColor: string;
  readonly cursorColor: string;
  readonly height: number;
  readonly responsive: boolean;
}

// Audio track interface for playback
export interface AudioTrack {
  readonly id: string;
  readonly name: string;
  readonly url: string;
  readonly metadata: AudioFileMetadata;
  readonly audioBuffer?: ArrayBuffer;
}

// Audio playback state
export interface AudioPlaybackState {
  readonly currentTrack: AudioTrack | null;
  readonly isPlaying: boolean;
  readonly currentTime: number;
  readonly duration: number;
  readonly volume: number;
  readonly isLoading: boolean;
  readonly error: string | null;
}