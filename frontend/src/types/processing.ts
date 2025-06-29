// Processing mode types
export type ProcessingMode = 'auto' | 'reference' | 'hybrid';
export type IntensityLevel = 'low' | 'medium' | 'high';
export type EQStyle = 'bright' | 'balanced' | 'warm' | 'auto';

export interface ProcessingSettings {
  readonly intensity: IntensityLevel;
  readonly eqStyle: EQStyle;
  readonly preserveDynamics: boolean;
  readonly targetLoudness: number; // LUFS (-23 to -6)
}

// Job status types
export type JobStatus = 
  | 'pending'
  | 'queued' 
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type ProcessingStage =
  | 'validation'
  | 'feature_extraction'
  | 'ai_analysis'
  | 'parameter_prediction'
  | 'audio_processing'
  | 'quality_check'
  | 'finalization';

export interface ProcessingProgress {
  readonly jobId: string;
  readonly status: JobStatus;
  readonly progress: number; // 0-100
  readonly currentStage: ProcessingStage;
  readonly message: string;
  readonly elapsedTime: number; // milliseconds
  readonly remainingTime: number | null; // milliseconds
}

// Validation functions
export const validateProcessingSettings = (settings: unknown): settings is ProcessingSettings => {
  if (typeof settings !== 'object' || settings === null) return false;
  
  const s = settings as Record<string, unknown>;
  
  return (
    ['low', 'medium', 'high'].includes(s.intensity as string) &&
    ['bright', 'balanced', 'warm', 'auto'].includes(s.eqStyle as string) &&
    typeof s.preserveDynamics === 'boolean' &&
    typeof s.targetLoudness === 'number' &&
    s.targetLoudness >= -23 &&
    s.targetLoudness <= -6
  );
};

export const validateIntensityLevel = (value: string): value is IntensityLevel => {
  return ['low', 'medium', 'high'].includes(value);
};

export const validateEQStyle = (value: string): value is EQStyle => {
  return ['bright', 'balanced', 'warm', 'auto'].includes(value);
};

export const validateProcessingMode = (value: string): value is ProcessingMode => {
  return ['auto', 'reference', 'hybrid'].includes(value);
};