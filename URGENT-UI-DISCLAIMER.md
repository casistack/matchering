# URGENT: UI Disclaimer Implementation

**Priority**: IMMEDIATE  
**Purpose**: Prevent user confusion about non-functional features

## Required Frontend Changes

### 1. **Add Warning Banner to AUTO Mode**
```tsx
// Add to frontend/src/pages/AutoMaster.tsx
const ModeWarning = () => (
  <Alert severity="warning" sx={{ mb: 2 }}>
    <AlertTitle>Development Notice</AlertTitle>
    AUTO mode is currently in development. For production-quality AI mastering, 
    please use HYBRID mode which features real AI processing.
  </Alert>
);
```

### 2. **Add Warning Banner to REFERENCE Mode**
```tsx
// Add to frontend/src/pages/ReferenceMaster.tsx (if exists)
const ReferenceWarning = () => (
  <Alert severity="warning" sx={{ mb: 2 }}>
    <AlertTitle>Development Notice</AlertTitle>
    REFERENCE mode is currently in development. For production-quality processing, 
    please use HYBRID mode.
  </Alert>
);
```

### 3. **Update Processing Mode Selection**
```tsx
// Update mode selection dropdown
const processingModes = [
  {
    value: 'hybrid',
    label: 'HYBRID (Recommended - AI + Matchering)',
    description: 'Production-ready AI-guided mastering',
    status: 'production'
  },
  {
    value: 'auto',
    label: 'AUTO (Development)',
    description: 'AI-only mastering - Currently in development',
    status: 'development',
    disabled: true  // Disable until implemented
  },
  {
    value: 'reference',
    label: 'REFERENCE (Development)',
    description: 'Traditional reference-based mastering - Currently in development',
    status: 'development',
    disabled: true  // Disable until implemented
  }
];
```

### 4. **Add Status Badges**
```tsx
const StatusBadge = ({ status }: { status: string }) => {
  const config = {
    production: { color: 'success', text: 'Production Ready' },
    development: { color: 'warning', text: 'In Development' },
    placeholder: { color: 'error', text: 'Not Functional' }
  };
  
  return (
    <Chip 
      label={config[status].text} 
      color={config[status].color} 
      size="small" 
    />
  );
};
```

## Backend Response Updates

### 1. **Add Status Warnings to API Responses**
```python
# Update audio_tasks.py to include warnings
def _generate_quality_metrics() -> Dict[str, Any]:
    return {
        "peak_level": -0.1,
        "lufs_integrated": -14.0,
        "dynamic_range": 8.0,
        "quality_score": 9.2,
        "warnings": [
            "DEVELOPMENT MODE: These metrics are placeholder values",
            "For production processing, use HYBRID mode"
        ]
    }
```

### 2. **Add Mode Status to Job Response**
```python
# Add to job creation response
{
    "job_id": "...",
    "status": "queued",
    "processing_mode": "auto",
    "mode_status": "development",
    "warnings": [
        "AUTO mode is currently in development",
        "Results may be placeholder values"
    ]
}
```

## Implementation Priority

1. **IMMEDIATE**: Disable AUTO/REFERENCE mode buttons
2. **URGENT**: Add warning banners to all processing pages
3. **HIGH**: Update API responses with honest warnings
4. **MEDIUM**: Add status badges to mode selection

This will prevent users from being misled while we implement the real functionality.