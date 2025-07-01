// Processing mode types - Enhanced 4-mode system
export type ProcessingMode = 'auto' | 'reference' | 'hybrid' | 'advanced';
export type IntensityLevel = 'low' | 'medium' | 'high';
export type EQStyle = 'bright' | 'balanced' | 'warm' | 'auto';

// Advanced mode specific types
export type ModelSelectionStrategy = 'auto' | 'speed' | 'quality' | 'custom';
export type EnsembleStrategy = 'weighted' | 'consensus' | 'best_model';
export type QualityPreference = 'speed' | 'balanced' | 'quality';
export type UserExperienceLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';
export type ProcessingComplexity = 'beginner' | 'intermediate' | 'advanced' | 'expert';
export type QualityLevel = 'good' | 'excellent' | 'professional' | 'research';
export type TimeConstraint = 'fast' | 'normal' | 'thorough';

export interface ProcessingSettings {
  readonly intensity: IntensityLevel;
  readonly eqStyle: EQStyle;
  readonly preserveDynamics: boolean;
  readonly targetLoudness: number; // LUFS (-23 to -6)
}

// Advanced mode specific options
export interface AdvancedModeOptions {
  readonly modelSelection: ModelSelectionStrategy;
  readonly ensembleStrategy: EnsembleStrategy;
  readonly styleDescription?: string; // For CLAP model guidance
  readonly qualityPreference: QualityPreference;
  readonly enableExperimental: boolean;
}

// Enhanced processing settings that include advanced options
export interface EnhancedProcessingSettings extends ProcessingSettings {
  readonly advancedOptions?: AdvancedModeOptions;
  readonly referenceTrack?: File; // For reference mode
}

// Processing mode information
export interface ProcessingModeInfo {
  readonly mode: ProcessingMode;
  readonly displayName: string;
  readonly description: string;
  readonly targetUsers: string[];
  readonly estimatedTime: string;
  readonly qualityLevel: QualityLevel;
  readonly complexity: ProcessingComplexity;
  readonly requiresReference: boolean;
  readonly supportsBatch: boolean;
}

// Audio characteristics for mode recommendation
export interface AudioCharacteristics {
  readonly genre: string;
  readonly hasVocals: boolean;
  readonly dynamicRange: number;
  readonly complexity: 'simple' | 'moderate' | 'complex';
  readonly duration: number;
  readonly quality: 'low' | 'medium' | 'high';
}

// Mode recommendation system
export interface ModeRecommendation {
  readonly recommendedMode: ProcessingMode;
  readonly confidence: number;
  readonly reasoning: string;
  readonly alternatives: Array<{
    mode: ProcessingMode;
    pros: string[];
    cons: string[];
  }>;
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
  return ['auto', 'reference', 'hybrid', 'advanced'].includes(value);
};

// Mode information constants
export const PROCESSING_MODES: Record<ProcessingMode, ProcessingModeInfo> = {
  auto: {
    mode: 'auto',
    displayName: 'AI Auto-Master',
    description: 'Fast, intelligent mastering using custom AI models',
    targetUsers: ['Content Creators', 'Podcasters', 'Quick Projects'],
    estimatedTime: '5-15 seconds',
    qualityLevel: 'good',
    complexity: 'beginner',
    requiresReference: false,
    supportsBatch: true
  },
  reference: {
    mode: 'reference',
    displayName: 'Reference-Based',
    description: 'Professional reference matching using proven DSP',
    targetUsers: ['Audio Engineers', 'Professionals', 'Traditional Workflow'],
    estimatedTime: '30-60 seconds',
    qualityLevel: 'professional',
    complexity: 'intermediate',
    requiresReference: true,
    supportsBatch: false
  },
  hybrid: {
    mode: 'hybrid',
    displayName: 'AI + Matchering',
    description: 'AI creates virtual reference for traditional processing',
    targetUsers: ['Professionals', 'AI-Assisted Workflow', 'Best of Both'],
    estimatedTime: '45-90 seconds',
    qualityLevel: 'excellent',
    complexity: 'intermediate',
    requiresReference: false,
    supportsBatch: true
  },
  advanced: {
    mode: 'advanced',
    displayName: 'Multi-Model AI',
    description: 'Cutting-edge ensemble AI using multiple pre-trained models',
    targetUsers: ['Researchers', 'Audiophiles', 'Cutting-Edge Production'],
    estimatedTime: '2-5 minutes',
    qualityLevel: 'research',
    complexity: 'expert',
    requiresReference: false,
    supportsBatch: false
  }
};

// Advanced mode validation
export const validateAdvancedModeOptions = (options: unknown): options is AdvancedModeOptions => {
  if (typeof options !== 'object' || options === null) return false;
  
  const o = options as Record<string, unknown>;
  
  return (
    ['auto', 'speed', 'quality', 'custom'].includes(o.modelSelection as string) &&
    ['weighted', 'consensus', 'best_model'].includes(o.ensembleStrategy as string) &&
    ['speed', 'balanced', 'quality'].includes(o.qualityPreference as string) &&
    typeof o.enableExperimental === 'boolean' &&
    (o.styleDescription === undefined || typeof o.styleDescription === 'string')
  );
};

// Mode recommendation utilities
export class ModeRecommendationEngine {
  static recommendMode(
    audioCharacteristics: AudioCharacteristics,
    userExperience: UserExperienceLevel = 'intermediate',
    timeConstraint: TimeConstraint = 'normal'
  ): ModeRecommendation {
    // Simple recommendation logic (can be enhanced with ML)
    let recommendedMode: ProcessingMode = 'auto';
    let confidence = 0.8;
    let reasoning = '';
    
    // Genre-based recommendations
    if (audioCharacteristics.genre.toLowerCase().includes('electronic') || 
        audioCharacteristics.genre.toLowerCase().includes('pop')) {
      if (userExperience === 'expert' && timeConstraint === 'thorough') {
        recommendedMode = 'advanced';
        reasoning = 'Electronic/pop music benefits from advanced AI models for optimal spectral processing';
        confidence = 0.9;
      } else if (audioCharacteristics.complexity === 'complex') {
        recommendedMode = 'hybrid';
        reasoning = 'Complex electronic music benefits from AI-guided traditional processing';
        confidence = 0.85;
      }
    } else if (audioCharacteristics.hasVocals && userExperience === 'intermediate') {
      recommendedMode = 'hybrid';
      reasoning = 'Vocal content benefits from AI analysis combined with proven Matchering processing';
      confidence = 0.88;
    }
    
    // Time constraint adjustments
    if (timeConstraint === 'fast') {
      recommendedMode = 'auto';
      reasoning = 'Auto mode provides fastest processing for time-constrained projects';
      confidence = 0.9;
    }
    
    // User experience adjustments
    if (userExperience === 'beginner') {
      recommendedMode = 'auto';
      reasoning = 'Auto mode is most user-friendly for beginners';
      confidence = 0.95;
    }
    
    return {
      recommendedMode,
      confidence,
      reasoning,
      alternatives: [
        {
          mode: 'auto',
          pros: ['Fastest processing', 'No reference needed', 'User-friendly'],
          cons: ['Basic quality', 'Less control']
        },
        {
          mode: 'hybrid',
          pros: ['Best of AI + traditional', 'Professional quality', 'No reference needed'],
          cons: ['Longer processing time', 'More complex']
        },
        {
          mode: 'advanced',
          pros: ['Highest quality', 'Cutting-edge AI', 'Research-grade'],
          cons: ['Longest processing time', 'Expert level complexity']
        }
      ]
    };
  }
}