#!/usr/bin/env python3
"""
Backend Schema Documentation Generator

This script reads the existing Pydantic schemas and generates comprehensive
documentation for frontend engineers. It does NOT modify any database schemas
or existing code - it only reads and documents what's already implemented.

Usage:
    python generate_schema_docs.py

Outputs:
    - frontend/docs/backend-api-schema.md (Markdown documentation)
    - frontend/docs/backend-schemas.json (JSON schema export)
    - frontend/docs/validation-rules.md (Validation reference)
"""

import json
import os
import sys
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.schemas.settings import (
        ModelPreferencesSchema,
        ModelPreferencesUpdateSchema,
        UserSettingsProfileSchema,
        UserSettingsProfileCreateSchema,
        UserSettingsProfileUpdateSchema,
        AvailableModelInfoSchema,
        ModelPerformanceInfoSchema,
        SettingsConfigResponse,
        SettingsUpdateResponse,
        ProfileSelectionResponse,
        UserSettingsAnalyticsSchema,
        SystemStatusResponse,
        ModelSelectionStrategy,
        QualityPreference,
        FallbackStrategy,
        ModelType
    )
    from app.schemas.processing import (
        ProcessingJobCreate,
        ProcessingJobResponse,
        ProcessingJobListResponse,
        ProcessingJobDetailResponse,
        JobProgressResponse,
        ProcessingStatsResponse,
        ProcessingModeInfo,
        ProcessingModesResponse,
        QueueStatusResponse
    )
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo
except ImportError as e:
    print(f"Error importing schemas: {e}")
    print("Make sure you're running this from the backend directory")
    sys.exit(1)

class SchemaDocumentationGenerator:
    """Generates comprehensive documentation from existing Pydantic schemas."""
    
    def __init__(self):
        self.schemas = {
            # Settings API schemas
            'ModelPreferencesSchema': ModelPreferencesSchema,
            'ModelPreferencesUpdateSchema': ModelPreferencesUpdateSchema,
            'UserSettingsProfileSchema': UserSettingsProfileSchema,
            'UserSettingsProfileCreateSchema': UserSettingsProfileCreateSchema,
            'UserSettingsProfileUpdateSchema': UserSettingsProfileUpdateSchema,
            'AvailableModelInfoSchema': AvailableModelInfoSchema,
            'ModelPerformanceInfoSchema': ModelPerformanceInfoSchema,
            'SettingsConfigResponse': SettingsConfigResponse,
            'SettingsUpdateResponse': SettingsUpdateResponse,
            'ProfileSelectionResponse': ProfileSelectionResponse,
            'UserSettingsAnalyticsSchema': UserSettingsAnalyticsSchema,
            'SystemStatusResponse': SystemStatusResponse,
            
            # Processing Jobs API schemas
            'ProcessingJobCreate': ProcessingJobCreate,
            'ProcessingJobResponse': ProcessingJobResponse,
            'ProcessingJobListResponse': ProcessingJobListResponse,
            'ProcessingJobDetailResponse': ProcessingJobDetailResponse,
            'JobProgressResponse': JobProgressResponse,
            'ProcessingStatsResponse': ProcessingStatsResponse,
            'ProcessingModeInfo': ProcessingModeInfo,
            'ProcessingModesResponse': ProcessingModesResponse,
            'QueueStatusResponse': QueueStatusResponse,
        }
        
        self.enums = {
            'ModelSelectionStrategy': ModelSelectionStrategy,
            'QualityPreference': QualityPreference,
            'FallbackStrategy': FallbackStrategy,
            'ModelType': ModelType,
        }
        
        self.api_endpoints = [
            # Settings API endpoints
            {
                'method': 'GET',
                'path': '/api/v1/settings/config',
                'description': 'Get complete user configuration',
                'query_params': ['anonymous_id (optional)', 'user_id (optional)'],
                'response_schema': 'SettingsConfigResponse',
                'example_response': 'settings_config_example'
            },
            {
                'method': 'PUT',
                'path': '/api/v1/settings/preferences',
                'description': 'Update user model preferences',
                'query_params': ['anonymous_id (optional)', 'user_id (optional)'],
                'request_schema': 'ModelPreferencesUpdateSchema',
                'response_schema': 'SettingsUpdateResponse',
                'example_request': 'preferences_update_example',
                'example_response': 'preferences_update_response_example'
            },
            {
                'method': 'POST',
                'path': '/api/v1/settings/profiles',
                'description': 'Create new settings profile',
                'query_params': ['anonymous_id (optional)', 'user_id (optional)'],
                'request_schema': 'UserSettingsProfileCreateSchema',
                'response_schema': 'UserSettingsProfileSchema'
            },
            {
                'method': 'GET',
                'path': '/api/v1/settings/profiles',
                'description': 'List all user profiles',
                'query_params': ['anonymous_id (optional)', 'user_id (optional)'],
                'response_schema': 'List[UserSettingsProfileSchema]'
            },
            {
                'method': 'PUT',
                'path': '/api/v1/settings/profiles/{profile_id}/select',
                'description': 'Select active profile',
                'path_params': ['profile_id (UUID)'],
                'query_params': ['anonymous_id (optional)', 'user_id (optional)'],
                'response_schema': 'ProfileSelectionResponse'
            },
            {
                'method': 'PUT',
                'path': '/api/v1/settings/profiles/{profile_id}',
                'description': 'Update existing profile',
                'path_params': ['profile_id (UUID)'],
                'query_params': ['anonymous_id (optional)', 'user_id (optional)'],
                'request_schema': 'UserSettingsProfileUpdateSchema',
                'response_schema': 'UserSettingsProfileSchema'
            },
            {
                'method': 'DELETE',
                'path': '/api/v1/settings/profiles/{profile_id}',
                'description': 'Delete profile',
                'path_params': ['profile_id (UUID)'],
                'query_params': ['anonymous_id (optional)', 'user_id (optional)'],
                'response_schema': '{"success": true}'
            },
            {
                'method': 'GET',
                'path': '/api/v1/settings/models',
                'description': 'Get available AI models',
                'response_schema': 'List[AvailableModelInfoSchema]'
            },
            {
                'method': 'GET',
                'path': '/api/v1/settings/analytics',
                'description': 'Get user analytics',
                'query_params': ['anonymous_id (optional)', 'days (optional, default=30)'],
                'response_schema': 'UserSettingsAnalyticsSchema'
            },
            {
                'method': 'GET',
                'path': '/api/v1/settings/system/status',
                'description': 'Get system status',
                'response_schema': 'SystemStatusResponse'
            },
            {
                'method': 'POST',
                'path': '/api/v1/settings/reset-defaults',
                'description': 'Reset to default preferences',
                'query_params': ['anonymous_id (optional)', 'user_id (optional)'],
                'response_schema': 'SettingsUpdateResponse'
            },
            
            # Processing Jobs API endpoints
            {
                'method': 'POST',
                'path': '/api/v1/processing/jobs',
                'description': 'Create new processing job',
                'request_schema': 'ProcessingJobCreate',
                'response_schema': 'ProcessingJobResponse'
            },
            {
                'method': 'GET',
                'path': '/api/v1/processing/jobs',
                'description': 'List processing jobs with pagination',
                'query_params': ['page (optional)', 'page_size (optional)', 'status (optional)', 'processing_mode (optional)'],
                'response_schema': 'ProcessingJobListResponse'
            },
            {
                'method': 'GET',
                'path': '/api/v1/processing/jobs/{job_id}',
                'description': 'Get detailed job information',
                'path_params': ['job_id (UUID)'],
                'response_schema': 'ProcessingJobDetailResponse'
            },
            {
                'method': 'POST',
                'path': '/api/v1/processing/jobs/{job_id}/cancel',
                'description': 'Cancel a processing job',
                'path_params': ['job_id (UUID)'],
                'response_schema': 'ProcessingJobResponse'
            },
            {
                'method': 'GET',
                'path': '/api/v1/processing/queue/status',
                'description': 'Get processing queue status',
                'response_schema': 'QueueStatusResponse'
            },
            {
                'method': 'GET',
                'path': '/api/v1/processing/stats',
                'description': 'Get processing statistics',
                'response_schema': 'ProcessingStatsResponse'
            },
            {
                'method': 'GET',
                'path': '/api/v1/processing/modes',
                'description': 'Get available processing modes',
                'response_schema': 'ProcessingModesResponse'
            },
            {
                'method': 'WebSocket',
                'path': '/api/v1/processing/ws/{job_id}',
                'description': 'Real-time processing progress updates',
                'path_params': ['job_id (UUID)'],
                'response_schema': 'JobProgressResponse'
            }
        ]

    def extract_field_info(self, model: BaseModel) -> Dict[str, Any]:
        """Extract field information from a Pydantic model."""
        fields_info = {}
        
        for field_name, field_info in model.model_fields.items():
            field_data = {
                'type': str(field_info.annotation) if field_info.annotation else 'Any',
                'required': field_info.is_required(),
                'default': field_info.default if field_info.default is not None else None,
                'description': field_info.description or '',
            }
            
            # Extract validation constraints
            if hasattr(field_info, 'constraints'):
                constraints = {}
                for constraint_name in ['gt', 'ge', 'lt', 'le', 'min_length', 'max_length']:
                    if hasattr(field_info, constraint_name):
                        value = getattr(field_info, constraint_name)
                        if value is not None:
                            constraints[constraint_name] = value
                if constraints:
                    field_data['constraints'] = constraints
            
            fields_info[field_name] = field_data
            
        return fields_info

    def generate_json_schema(self) -> Dict[str, Any]:
        """Generate JSON schema export."""
        json_schema = {
            'generated_at': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'description': 'Backend API Schemas for Matchering Settings and Processing Jobs',
            'schemas': {},
            'enums': {},
            'api_endpoints': self.api_endpoints
        }
        
        # Extract schema information
        for schema_name, schema_class in self.schemas.items():
            try:
                json_schema['schemas'][schema_name] = {
                    'description': schema_class.__doc__ or f'{schema_name} schema',
                    'fields': self.extract_field_info(schema_class),
                    'json_schema': schema_class.model_json_schema()
                }
            except Exception as e:
                print(f"Warning: Could not process {schema_name}: {e}")
        
        # Extract enum information
        for enum_name, enum_class in self.enums.items():
            json_schema['enums'][enum_name] = {
                'description': enum_class.__doc__ or f'{enum_name} enumeration',
                'values': [item.value for item in enum_class]
            }
        
        return json_schema

    def generate_markdown_docs(self, json_schema: Dict[str, Any]) -> str:
        """Generate comprehensive markdown documentation."""
        
        md = f"""# Backend API Schema Documentation

**Generated:** {json_schema['generated_at']}  
**Version:** {json_schema['version']}

This document provides comprehensive reference documentation for the Matchering backend API schemas. All schemas are auto-generated from the actual Pydantic models to ensure accuracy.

## Table of Contents

1. [API Endpoints](#api-endpoints)
   - [Settings Management](#settings-management)
   - [Processing Jobs Management](#processing-jobs-management)
2. [Request/Response Schemas](#requestresponse-schemas)
3. [Enumerations](#enumerations)
4. [Validation Rules](#validation-rules)
5. [Common Examples](#common-examples)

## API Endpoints

### Settings Management

"""
        
        # Generate API endpoint documentation
        settings_endpoints = [ep for ep in json_schema['api_endpoints'] if ep['path'].startswith('/api/v1/settings')]
        processing_endpoints = [ep for ep in json_schema['api_endpoints'] if ep['path'].startswith('/api/v1/processing')]
        
        # Settings endpoints
        for endpoint in settings_endpoints:
            md += f"#### {endpoint['method']} `{endpoint['path']}`\n\n"
            md += f"**Description:** {endpoint['description']}\n\n"
            
            if endpoint.get('path_params'):
                md += "**Path Parameters:**\n"
                for param in endpoint['path_params']:
                    md += f"- `{param}`\n"
                md += "\n"
            
            if endpoint.get('query_params'):
                md += "**Query Parameters:**\n"
                for param in endpoint['query_params']:
                    md += f"- `{param}`\n"
                md += "\n"
            
            if endpoint.get('request_schema'):
                md += f"**Request Schema:** [{endpoint['request_schema']}](#{endpoint['request_schema'].lower()})\n\n"
            
            if endpoint.get('response_schema'):
                md += f"**Response Schema:** [{endpoint['response_schema']}](#{endpoint['response_schema'].lower().replace('[', '').replace(']', '').replace('<', '').replace('>', '')})\n\n"
            
            md += "---\n\n"

        # Processing Jobs endpoints
        md += "### Processing Jobs Management\n\n"
        
        for endpoint in processing_endpoints:
            md += f"#### {endpoint['method']} `{endpoint['path']}`\n\n"
            md += f"**Description:** {endpoint['description']}\n\n"
            
            if endpoint.get('path_params'):
                md += "**Path Parameters:**\n"
                for param in endpoint['path_params']:
                    md += f"- `{param}`\n"
                md += "\n"
            
            if endpoint.get('query_params'):
                md += "**Query Parameters:**\n"
                for param in endpoint['query_params']:
                    md += f"- `{param}`\n"
                md += "\n"
            
            if endpoint.get('request_schema'):
                md += f"**Request Schema:** [{endpoint['request_schema']}](#{endpoint['request_schema'].lower()})\n\n"
            
            if endpoint.get('response_schema'):
                md += f"**Response Schema:** [{endpoint['response_schema']}](#{endpoint['response_schema'].lower().replace('[', '').replace(']', '').replace('<', '').replace('>', '')})\n\n"
            
            md += "---\n\n"

        md += "## Request/Response Schemas\n\n"
        
        # Generate schema documentation
        for schema_name, schema_info in json_schema['schemas'].items():
            md += f"### {schema_name}\n\n"
            md += f"**Description:** {schema_info['description']}\n\n"
            
            md += "**Fields:**\n\n"
            md += "| Field | Type | Required | Default | Description | Constraints |\n"
            md += "|-------|------|----------|---------|-------------|-------------|\n"
            
            for field_name, field_info in schema_info['fields'].items():
                required = "✅" if field_info['required'] else "❌"
                default = str(field_info['default']) if field_info['default'] is not None else "None"
                constraints = str(field_info.get('constraints', '')) if field_info.get('constraints') else ""
                
                md += f"| `{field_name}` | `{field_info['type']}` | {required} | `{default}` | {field_info['description']} | {constraints} |\n"
            
            md += "\n"
            
            # Add JSON schema
            md += "**JSON Schema:**\n```json\n"
            md += json.dumps(schema_info['json_schema'], indent=2)
            md += "\n```\n\n"
            
            md += "---\n\n"

        md += "## Enumerations\n\n"
        
        # Generate enum documentation
        for enum_name, enum_info in json_schema['enums'].items():
            md += f"### {enum_name}\n\n"
            md += f"**Description:** {enum_info['description']}\n\n"
            md += "**Valid Values:**\n"
            for value in enum_info['values']:
                md += f"- `{value}`\n"
            md += "\n---\n\n"

        md += """## Validation Rules

### Critical Validation Requirements

#### Settings API Validation

##### Ensemble Weights
- **Must sum to approximately 1.0** (between 0.9 and 1.1)
- **Example:** `{"huggingface_ensemble": 0.7, "ast_model": 0.25, "fallback_classifier": 0.05}`
- **Total:** 0.7 + 0.25 + 0.05 = 1.0 ✅

##### Confidence Threshold  
- **Range:** 0.5 ≤ value ≤ 0.95
- **Example:** `0.6` ✅, `0.4` ❌, `0.98` ❌

##### Max Processing Time
- **Range:** 1000 ≤ value ≤ 10000 (milliseconds)
- **Example:** `5000` ✅, `500` ❌, `15000` ❌

##### Model IDs (Current)
- **HuggingFace Ensemble:** `huggingface_ensemble`
- **Audio Spectrogram Transformer:** `ast_model`  
- **Fallback Classifier:** `fallback_classifier`

#### Processing Jobs API Validation

##### Required Fields (POST /api/v1/processing/jobs)
- **input_file_id:** Required UUID - ID of the uploaded audio file
- **processing_mode:** Required string - Must be one of: `"auto"`, `"reference"`, `"hybrid"`
- **settings:** Optional Dict[str, Any] - Processing configuration settings

##### Optional Fields
- **reference_file_id:** Optional UUID - Required only for `"reference"` processing mode
- **priority:** Optional integer - Range: 1-10 (1=highest, 10=lowest), default: 5

##### Processing Mode Validation
- **auto:** AI-based mastering (no reference file required)
- **reference:** Reference-based mastering (reference_file_id required)
- **hybrid:** Combination of AI and reference mastering

##### UUID Format
- **All file IDs must be valid UUIDs**
- **Example:** `"ccb9b7e1-cb72-4598-9d45-cde2d33d61e9"` ✅
- **Invalid:** `"invalid-uuid"` ❌

## Common Examples

### Settings API Examples

#### Update Model Preferences

```json
{
  "ensemble_weights": {
    "huggingface_ensemble": 0.7,
    "ast_model": 0.25,
    "fallback_classifier": 0.05
  },
  "confidence_threshold": 0.6,
  "max_processing_time": 5000,
  "preferred_strategy": "auto",
  "quality_preference": "balanced",
  "fallback_strategy": "graceful",
  "enable_experimental": false
}
```

#### Create New Profile

```json
{
  "name": "My Custom Profile",
  "description": "Optimized for electronic music",
  "preferences": {
    "preferred_strategy": "quality",
    "ensemble_weights": {
      "huggingface_ensemble": 0.8,
      "ast_model": 0.15,
      "fallback_classifier": 0.05
    },
    "quality_preference": "quality",
    "confidence_threshold": 0.8,
    "max_processing_time": 8000,
    "fallback_strategy": "graceful",
    "enable_experimental": true,
    "custom_settings": {}
  }
}
```

### Processing Jobs API Examples

#### Create Processing Job (Auto Mode)

```json
{
  "input_file_id": "ccb9b7e1-cb72-4598-9d45-cde2d33d61e9",
  "processing_mode": "auto",
  "settings": {
    "intensity": "medium",
    "eqStyle": "balanced",
    "preserveDynamics": true,
    "targetLoudness": -14.5
  },
  "priority": 5
}
```

#### Create Processing Job (Reference Mode)

```json
{
  "input_file_id": "ccb9b7e1-cb72-4598-9d45-cde2d33d61e9",
  "reference_file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "processing_mode": "reference",
  "settings": {
    "intensity": "high",
    "preserveOriginalDynamics": false
  },
  "priority": 3
}
```

#### Create Processing Job (Hybrid Mode)

```json
{
  "input_file_id": "ccb9b7e1-cb72-4598-9d45-cde2d33d61e9",
  "reference_file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "processing_mode": "hybrid",
  "settings": {
    "aiWeight": 0.7,
    "referenceWeight": 0.3,
    "intensity": "medium",
    "targetLoudness": -16.0
  },
  "priority": 4
}
```

### Error Response Format

```json
{
  "detail": "Ensemble weights must sum to approximately 1.0, got 0.8",
  "statusCode": 422,
  "field": "ensemble_weights"
}
```

## Notes for Frontend Engineers

### General Guidelines

1. **Always validate data locally** before sending to backend
2. **Use the exact enum values** listed in this document  
3. **Handle 422 validation errors** gracefully
4. **Use anonymous_id** for unauthenticated users
5. **All timestamps** are in ISO format (UTC)

### Settings API Guidelines

1. **Ensure ensemble weights sum to ~1.0** before submission
2. **Check value ranges** for numeric fields
3. **Use proper confidence threshold ranges** (0.5-0.95)

### Processing Jobs API Guidelines

1. **Use correct field names:**
   - ✅ `input_file_id` (not `fileId`)
   - ✅ `processing_mode` (not `mode`)
   - ✅ `reference_file_id` (not `referenceFileId`)

2. **Validate processing mode requirements:**
   - `auto`: No reference file needed
   - `reference`: Reference file required
   - `hybrid`: Reference file required

3. **Handle UUIDs properly:**
   - Always use valid UUID format
   - Validate UUIDs before sending requests

4. **Common 422 validation errors:**
   - Missing required fields (`input_file_id`, `processing_mode`)
   - Invalid processing mode value
   - Invalid UUID format
   - Reference file missing for reference/hybrid modes

### Field Name Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Notes |
|----------------|---------------|-------|
| `fileId` | `input_file_id` | ❌ Use `input_file_id` |
| `mode` | `processing_mode` | ❌ Use `processing_mode` |
| `referenceFileId` | `reference_file_id` | ❌ Use `reference_file_id` |
| `priority` | `priority` | ✅ Same field name |
| `settings` | `settings` | ✅ Same field name |

---

*This documentation is auto-generated from the actual backend schemas. Last updated: {json_schema['generated_at']}*
"""
        
        return md

    def generate_validation_reference(self) -> str:
        """Generate a quick validation reference guide."""
        
        return """# Backend Validation Reference Guide

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
"""

    def generate_all_documentation(self):
        """Generate all documentation files."""
        
        print("🔧 Generating backend schema documentation...")
        
        # Create frontend/docs directory if it doesn't exist
        docs_dir = Path("../frontend/docs")
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate JSON schema
        print("📄 Extracting schemas from Pydantic models...")
        json_schema = self.generate_json_schema()
        
        # Write JSON schema file
        json_file = docs_dir / "backend-schemas.json"
        with open(json_file, 'w') as f:
            json.dump(json_schema, f, indent=2, default=str)
        print(f"✅ Generated: {json_file}")
        
        # Generate markdown documentation
        print("📝 Generating comprehensive markdown documentation...")
        markdown_docs = self.generate_markdown_docs(json_schema)
        
        md_file = docs_dir / "backend-api-schema.md"
        with open(md_file, 'w') as f:
            f.write(markdown_docs)
        print(f"✅ Generated: {md_file}")
        
        # Generate validation reference
        print("🔍 Generating validation reference guide...")
        validation_docs = self.generate_validation_reference()
        
        validation_file = docs_dir / "validation-rules.md"
        with open(validation_file, 'w') as f:
            f.write(validation_docs)
        print(f"✅ Generated: {validation_file}")
        
        print(f"\n🎉 Documentation generation complete!")
        print(f"📁 Files created in: {docs_dir.absolute()}")
        print(f"📚 View documentation at:")
        print(f"   - {md_file}")
        print(f"   - {validation_file}")
        print(f"   - {json_file}")

if __name__ == "__main__":
    generator = SchemaDocumentationGenerator()
    generator.generate_all_documentation()