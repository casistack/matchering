# Backend Validation Reference Guide

## Quick Validation Checklist

### Settings API Validation

#### ✅ Ensemble Weights
```typescript
const total = Object.values(ensembleWeights).reduce((sum, weight) => sum + weight, 0);
const isValid = total >= 0.9 && total <= 1.1;
```

#### ✅ Confidence Threshold
```typescript
const isValid = threshold >= 0.5 && threshold <= 0.95;
```

#### ✅ Max Processing Time
```typescript
const isValid = time >= 1000 && time <= 10000; // milliseconds
```

### Processing Jobs API Validation

#### ✅ Processing Job Create Request
```typescript
interface ProcessingJobCreateRequest {
  input_file_id: string;        // Required: UUID of uploaded file
  processing_mode: 'auto' | 'reference' | 'hybrid';  // Required
  reference_file_id?: string;   // Optional: Required for reference/hybrid modes
  settings?: Record<string, any>;  // Optional: Processing settings
  priority?: number;            // Optional: 1-10 (1=highest, 10=lowest)
}
```

#### ✅ Field Name Validation
```typescript
// ❌ INCORRECT (frontend style)
const wrongRequest = {
  fileId: "uuid-here",
  mode: "auto"
};

// ✅ CORRECT (backend expected)
const correctRequest = {
  input_file_id: "uuid-here",
  processing_mode: "auto"
};
```

#### ✅ UUID Validation
```typescript
const isValidUUID = (uuid: string): boolean => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
};
```

#### ✅ Processing Mode Validation
```typescript
const isValidProcessingMode = (mode: string): boolean => {
  return ['auto', 'reference', 'hybrid'].includes(mode);
};
```

### ✅ Valid Enum Values

**ModelSelectionStrategy:**
- `auto` - Automatic model selection
- `performance` - Optimize for speed  
- `quality` - Optimize for accuracy
- `custom` - User-defined weights

**QualityPreference:**
- `fast` - Prioritize speed
- `balanced` - Balance speed and quality
- `quality` - Prioritize accuracy

**FallbackStrategy:**
- `strict` - Fail if confidence too low
- `graceful` - Use fallback model
- `aggressive` - Always attempt processing

### ✅ Current Model IDs
- `huggingface_ensemble` - HuggingFace Ensemble
- `ast_model` - Audio Spectrogram Transformer  
- `fallback_classifier` - Fallback Classifier

### ❌ Common Validation Errors

**422 Unprocessable Entity (Settings API):**
- Ensemble weights don't sum to ~1.0
- Confidence threshold out of range (0.5-0.95)
- Processing time out of range (1000-10000ms)
- Invalid enum value
- Missing required fields

**422 Unprocessable Entity (Processing Jobs API):**
- Missing required fields (`input_file_id`, `processing_mode`)
- Invalid processing mode (must be: auto, reference, hybrid)
- Invalid UUID format for file IDs
- Reference file missing for reference/hybrid modes
- Priority out of range (1-10)

**400 Bad Request:**
- Missing anonymous_id or user_id
- Invalid UUID format for profile_id
- Malformed JSON payload

### 🔧 Frontend Validation Helpers

#### Settings API Validation
```typescript
export const validatePreferences = (prefs: Partial<ModelPreferences>): string[] => {
  const errors: string[] = [];
  
  if (prefs.ensemble_weights) {
    const total = Object.values(prefs.ensemble_weights).reduce((sum, w) => sum + w, 0);
    if (total < 0.9 || total > 1.1) {
      errors.push(`Ensemble weights must sum to ~1.0, got ${total.toFixed(3)}`);
    }
  }
  
  if (prefs.confidence_threshold !== undefined) {
    if (prefs.confidence_threshold < 0.5 || prefs.confidence_threshold > 0.95) {
      errors.push(`Confidence threshold must be 0.5-0.95, got ${prefs.confidence_threshold}`);
    }
  }
  
  if (prefs.max_processing_time !== undefined) {
    if (prefs.max_processing_time < 1000 || prefs.max_processing_time > 10000) {
      errors.push(`Max processing time must be 1000-10000ms, got ${prefs.max_processing_time}`);
    }
  }
  
  return errors;
};
```

#### Processing Jobs API Validation
```typescript
export const validateProcessingJobCreate = (job: any): string[] => {
  const errors: string[] = [];
  
  // Required fields
  if (!job.input_file_id) {
    errors.push('input_file_id is required');
  } else if (!isValidUUID(job.input_file_id)) {
    errors.push('input_file_id must be a valid UUID');
  }
  
  if (!job.processing_mode) {
    errors.push('processing_mode is required');
  } else if (!['auto', 'reference', 'hybrid'].includes(job.processing_mode)) {
    errors.push('processing_mode must be one of: auto, reference, hybrid');
  }
  
  // Reference file validation
  if (['reference', 'hybrid'].includes(job.processing_mode)) {
    if (!job.reference_file_id) {
      errors.push(`reference_file_id is required for ${job.processing_mode} mode`);
    } else if (!isValidUUID(job.reference_file_id)) {
      errors.push('reference_file_id must be a valid UUID');
    }
  }
  
  // Priority validation
  if (job.priority !== undefined) {
    if (job.priority < 1 || job.priority > 10) {
      errors.push('priority must be between 1 and 10');
    }
  }
  
  return errors;
};

const isValidUUID = (uuid: string): boolean => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
};
```
