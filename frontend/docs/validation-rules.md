# Backend Validation Reference Guide

## Quick Validation Checklist

### ✅ Ensemble Weights
```typescript
const total = Object.values(ensembleWeights).reduce((sum, weight) => sum + weight, 0);
const isValid = total >= 0.9 && total <= 1.1;
```

### ✅ Confidence Threshold
```typescript
const isValid = threshold >= 0.5 && threshold <= 0.95;
```

### ✅ Max Processing Time
```typescript
const isValid = time >= 1000 && time <= 10000; // milliseconds
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

**422 Unprocessable Entity:**
- Ensemble weights don't sum to ~1.0
- Confidence threshold out of range (0.5-0.95)
- Processing time out of range (1000-10000ms)
- Invalid enum value
- Missing required fields

**400 Bad Request:**
- Missing anonymous_id or user_id
- Invalid UUID format for profile_id
- Malformed JSON payload

### 🔧 Frontend Validation Helper

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
