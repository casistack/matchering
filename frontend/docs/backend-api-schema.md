# Backend API Schema Documentation

**Generated:** 2025-07-06T13:34:49.108192  
**Version:** 1.0.0

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

#### GET `/api/v1/settings/config`

**Description:** Get complete user configuration

**Query Parameters:**
- `anonymous_id (optional)`
- `user_id (optional)`

**Response Schema:** [SettingsConfigResponse](#settingsconfigresponse)

---

#### PUT `/api/v1/settings/preferences`

**Description:** Update user model preferences

**Query Parameters:**
- `anonymous_id (optional)`
- `user_id (optional)`

**Request Schema:** [ModelPreferencesUpdateSchema](#modelpreferencesupdateschema)

**Response Schema:** [SettingsUpdateResponse](#settingsupdateresponse)

---

#### POST `/api/v1/settings/profiles`

**Description:** Create new settings profile

**Query Parameters:**
- `anonymous_id (optional)`
- `user_id (optional)`

**Request Schema:** [UserSettingsProfileCreateSchema](#usersettingsprofilecreateschema)

**Response Schema:** [UserSettingsProfileSchema](#usersettingsprofileschema)

---

#### GET `/api/v1/settings/profiles`

**Description:** List all user profiles

**Query Parameters:**
- `anonymous_id (optional)`
- `user_id (optional)`

**Response Schema:** [List[UserSettingsProfileSchema]](#listusersettingsprofileschema)

---

#### PUT `/api/v1/settings/profiles/{profile_id}/select`

**Description:** Select active profile

**Path Parameters:**
- `profile_id (UUID)`

**Query Parameters:**
- `anonymous_id (optional)`
- `user_id (optional)`

**Response Schema:** [ProfileSelectionResponse](#profileselectionresponse)

---

#### PUT `/api/v1/settings/profiles/{profile_id}`

**Description:** Update existing profile

**Path Parameters:**
- `profile_id (UUID)`

**Query Parameters:**
- `anonymous_id (optional)`
- `user_id (optional)`

**Request Schema:** [UserSettingsProfileUpdateSchema](#usersettingsprofileupdateschema)

**Response Schema:** [UserSettingsProfileSchema](#usersettingsprofileschema)

---

#### DELETE `/api/v1/settings/profiles/{profile_id}`

**Description:** Delete profile

**Path Parameters:**
- `profile_id (UUID)`

**Query Parameters:**
- `anonymous_id (optional)`
- `user_id (optional)`

**Response Schema:** [{"success": true}](#{"success": true})

---

#### GET `/api/v1/settings/models`

**Description:** Get available AI models

**Response Schema:** [List[AvailableModelInfoSchema]](#listavailablemodelinfoschema)

---

#### GET `/api/v1/settings/analytics`

**Description:** Get user analytics

**Query Parameters:**
- `anonymous_id (optional)`
- `days (optional, default=30)`

**Response Schema:** [UserSettingsAnalyticsSchema](#usersettingsanalyticsschema)

---

#### GET `/api/v1/settings/system/status`

**Description:** Get system status

**Response Schema:** [SystemStatusResponse](#systemstatusresponse)

---

#### POST `/api/v1/settings/reset-defaults`

**Description:** Reset to default preferences

**Query Parameters:**
- `anonymous_id (optional)`
- `user_id (optional)`

**Response Schema:** [SettingsUpdateResponse](#settingsupdateresponse)

---

### Processing Jobs Management

#### POST `/api/v1/processing/jobs`

**Description:** Create new processing job

**Request Schema:** [ProcessingJobCreate](#processingjobcreate)

**Response Schema:** [ProcessingJobResponse](#processingjobresponse)

---

#### GET `/api/v1/processing/jobs`

**Description:** List processing jobs with pagination

**Query Parameters:**
- `page (optional)`
- `page_size (optional)`
- `status (optional)`
- `processing_mode (optional)`

**Response Schema:** [ProcessingJobListResponse](#processingjoblistresponse)

---

#### GET `/api/v1/processing/jobs/{job_id}`

**Description:** Get detailed job information

**Path Parameters:**
- `job_id (UUID)`

**Response Schema:** [ProcessingJobDetailResponse](#processingjobdetailresponse)

---

#### POST `/api/v1/processing/jobs/{job_id}/cancel`

**Description:** Cancel a processing job

**Path Parameters:**
- `job_id (UUID)`

**Response Schema:** [ProcessingJobResponse](#processingjobresponse)

---

#### GET `/api/v1/processing/queue/status`

**Description:** Get processing queue status

**Response Schema:** [QueueStatusResponse](#queuestatusresponse)

---

#### GET `/api/v1/processing/stats`

**Description:** Get processing statistics

**Response Schema:** [ProcessingStatsResponse](#processingstatsresponse)

---

#### GET `/api/v1/processing/modes`

**Description:** Get available processing modes

**Response Schema:** [ProcessingModesResponse](#processingmodesresponse)

---

#### WebSocket `/api/v1/processing/ws/{job_id}`

**Description:** Real-time processing progress updates

**Path Parameters:**
- `job_id (UUID)`

**Response Schema:** [JobProgressResponse](#jobprogressresponse)

---

## Request/Response Schemas

### ModelPreferencesSchema

**Description:** User's model selection preferences.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `preferred_strategy` | `<enum 'ModelSelectionStrategy'>` | ❌ | `ModelSelectionStrategy.AUTO` |  |  |
| `ensemble_weights` | `typing.Dict[str, float]` | ❌ | `{'huggingface_ensemble': 0.7, 'ast_model': 0.25, 'fallback_classifier': 0.05}` | Weights for ensemble models |  |
| `quality_preference` | `<enum 'QualityPreference'>` | ❌ | `QualityPreference.BALANCED` |  |  |
| `enable_experimental` | `<class 'bool'>` | ❌ | `False` | Enable experimental features |  |
| `confidence_threshold` | `<class 'float'>` | ❌ | `0.6` | Minimum confidence threshold |  |
| `max_processing_time` | `<class 'int'>` | ❌ | `5000` | Max processing time in milliseconds |  |
| `fallback_strategy` | `<enum 'FallbackStrategy'>` | ❌ | `FallbackStrategy.GRACEFUL` |  |  |
| `custom_settings` | `typing.Dict[str, typing.Any]` | ❌ | `{}` | Custom user settings |  |

**JSON Schema:**
```json
{
  "$defs": {
    "FallbackStrategy": {
      "description": "Fallback strategy when primary models fail.",
      "enum": [
        "strict",
        "graceful",
        "aggressive"
      ],
      "title": "FallbackStrategy",
      "type": "string"
    },
    "ModelSelectionStrategy": {
      "description": "Model selection strategy options.",
      "enum": [
        "auto",
        "performance",
        "quality",
        "custom"
      ],
      "title": "ModelSelectionStrategy",
      "type": "string"
    },
    "QualityPreference": {
      "description": "Quality vs speed preference options.",
      "enum": [
        "fast",
        "balanced",
        "quality"
      ],
      "title": "QualityPreference",
      "type": "string"
    }
  },
  "description": "User's model selection preferences.",
  "properties": {
    "preferred_strategy": {
      "$ref": "#/$defs/ModelSelectionStrategy",
      "default": "auto"
    },
    "ensemble_weights": {
      "additionalProperties": {
        "type": "number"
      },
      "default": {
        "huggingface_ensemble": 0.7,
        "ast_model": 0.25,
        "fallback_classifier": 0.05
      },
      "description": "Weights for ensemble models",
      "title": "Ensemble Weights",
      "type": "object"
    },
    "quality_preference": {
      "$ref": "#/$defs/QualityPreference",
      "default": "balanced"
    },
    "enable_experimental": {
      "default": false,
      "description": "Enable experimental features",
      "title": "Enable Experimental",
      "type": "boolean"
    },
    "confidence_threshold": {
      "default": 0.6,
      "description": "Minimum confidence threshold",
      "maximum": 0.95,
      "minimum": 0.5,
      "title": "Confidence Threshold",
      "type": "number"
    },
    "max_processing_time": {
      "default": 5000,
      "description": "Max processing time in milliseconds",
      "maximum": 10000,
      "minimum": 1000,
      "title": "Max Processing Time",
      "type": "integer"
    },
    "fallback_strategy": {
      "$ref": "#/$defs/FallbackStrategy",
      "default": "graceful"
    },
    "custom_settings": {
      "additionalProperties": true,
      "default": {},
      "description": "Custom user settings",
      "title": "Custom Settings",
      "type": "object"
    }
  },
  "title": "ModelPreferencesSchema",
  "type": "object"
}
```

---

### ModelPreferencesUpdateSchema

**Description:** Schema for updating model preferences.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `preferred_strategy` | `typing.Optional[app.schemas.settings.ModelSelectionStrategy]` | ❌ | `None` |  |  |
| `ensemble_weights` | `typing.Optional[typing.Dict[str, float]]` | ❌ | `None` |  |  |
| `quality_preference` | `typing.Optional[app.schemas.settings.QualityPreference]` | ❌ | `None` |  |  |
| `enable_experimental` | `typing.Optional[bool]` | ❌ | `None` |  |  |
| `confidence_threshold` | `typing.Optional[float]` | ❌ | `None` |  |  |
| `max_processing_time` | `typing.Optional[int]` | ❌ | `None` |  |  |
| `fallback_strategy` | `typing.Optional[app.schemas.settings.FallbackStrategy]` | ❌ | `None` |  |  |
| `custom_settings` | `typing.Optional[typing.Dict[str, typing.Any]]` | ❌ | `None` |  |  |

**JSON Schema:**
```json
{
  "$defs": {
    "FallbackStrategy": {
      "description": "Fallback strategy when primary models fail.",
      "enum": [
        "strict",
        "graceful",
        "aggressive"
      ],
      "title": "FallbackStrategy",
      "type": "string"
    },
    "ModelSelectionStrategy": {
      "description": "Model selection strategy options.",
      "enum": [
        "auto",
        "performance",
        "quality",
        "custom"
      ],
      "title": "ModelSelectionStrategy",
      "type": "string"
    },
    "QualityPreference": {
      "description": "Quality vs speed preference options.",
      "enum": [
        "fast",
        "balanced",
        "quality"
      ],
      "title": "QualityPreference",
      "type": "string"
    }
  },
  "description": "Schema for updating model preferences.",
  "properties": {
    "preferred_strategy": {
      "anyOf": [
        {
          "$ref": "#/$defs/ModelSelectionStrategy"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "ensemble_weights": {
      "anyOf": [
        {
          "additionalProperties": {
            "type": "number"
          },
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Ensemble Weights"
    },
    "quality_preference": {
      "anyOf": [
        {
          "$ref": "#/$defs/QualityPreference"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "enable_experimental": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Enable Experimental"
    },
    "confidence_threshold": {
      "anyOf": [
        {
          "maximum": 0.95,
          "minimum": 0.5,
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Confidence Threshold"
    },
    "max_processing_time": {
      "anyOf": [
        {
          "maximum": 10000,
          "minimum": 1000,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Max Processing Time"
    },
    "fallback_strategy": {
      "anyOf": [
        {
          "$ref": "#/$defs/FallbackStrategy"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "custom_settings": {
      "anyOf": [
        {
          "additionalProperties": true,
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Custom Settings"
    }
  },
  "title": "ModelPreferencesUpdateSchema",
  "type": "object"
}
```

---

### UserSettingsProfileSchema

**Description:** Complete user settings profile.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `id` | `<class 'str'>` | ✅ | `PydanticUndefined` |  |  |
| `name` | `<class 'str'>` | ✅ | `PydanticUndefined` |  |  |
| `description` | `typing.Optional[str]` | ❌ | `None` |  |  |
| `preferred_strategy` | `<enum 'ModelSelectionStrategy'>` | ✅ | `PydanticUndefined` |  |  |
| `ensemble_weights` | `typing.Dict[str, float]` | ✅ | `PydanticUndefined` |  |  |
| `quality_preference` | `<enum 'QualityPreference'>` | ✅ | `PydanticUndefined` |  |  |
| `enable_experimental` | `<class 'bool'>` | ✅ | `PydanticUndefined` |  |  |
| `confidence_threshold` | `<class 'float'>` | ✅ | `PydanticUndefined` |  |  |
| `max_processing_time` | `<class 'int'>` | ✅ | `PydanticUndefined` |  |  |
| `fallback_strategy` | `<enum 'FallbackStrategy'>` | ✅ | `PydanticUndefined` |  |  |
| `advanced_settings` | `typing.Dict[str, typing.Any]` | ❌ | `{}` |  |  |
| `feature_flags` | `typing.Dict[str, typing.Any]` | ❌ | `{}` |  |  |
| `is_default` | `<class 'bool'>` | ❌ | `False` |  |  |
| `is_custom` | `<class 'bool'>` | ❌ | `False` |  |  |
| `is_system_profile` | `<class 'bool'>` | ❌ | `False` |  |  |
| `usage_count` | `<class 'int'>` | ❌ | `0` |  |  |
| `created_at` | `<class 'datetime.datetime'>` | ✅ | `PydanticUndefined` |  |  |
| `updated_at` | `<class 'datetime.datetime'>` | ✅ | `PydanticUndefined` |  |  |
| `last_used` | `typing.Optional[datetime.datetime]` | ❌ | `None` |  |  |

**JSON Schema:**
```json
{
  "$defs": {
    "FallbackStrategy": {
      "description": "Fallback strategy when primary models fail.",
      "enum": [
        "strict",
        "graceful",
        "aggressive"
      ],
      "title": "FallbackStrategy",
      "type": "string"
    },
    "ModelSelectionStrategy": {
      "description": "Model selection strategy options.",
      "enum": [
        "auto",
        "performance",
        "quality",
        "custom"
      ],
      "title": "ModelSelectionStrategy",
      "type": "string"
    },
    "QualityPreference": {
      "description": "Quality vs speed preference options.",
      "enum": [
        "fast",
        "balanced",
        "quality"
      ],
      "title": "QualityPreference",
      "type": "string"
    }
  },
  "description": "Complete user settings profile.",
  "properties": {
    "id": {
      "title": "Id",
      "type": "string"
    },
    "name": {
      "maxLength": 100,
      "minLength": 1,
      "title": "Name",
      "type": "string"
    },
    "description": {
      "anyOf": [
        {
          "maxLength": 500,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Description"
    },
    "preferred_strategy": {
      "$ref": "#/$defs/ModelSelectionStrategy"
    },
    "ensemble_weights": {
      "additionalProperties": {
        "type": "number"
      },
      "title": "Ensemble Weights",
      "type": "object"
    },
    "quality_preference": {
      "$ref": "#/$defs/QualityPreference"
    },
    "enable_experimental": {
      "title": "Enable Experimental",
      "type": "boolean"
    },
    "confidence_threshold": {
      "title": "Confidence Threshold",
      "type": "number"
    },
    "max_processing_time": {
      "title": "Max Processing Time",
      "type": "integer"
    },
    "fallback_strategy": {
      "$ref": "#/$defs/FallbackStrategy"
    },
    "advanced_settings": {
      "additionalProperties": true,
      "default": {},
      "title": "Advanced Settings",
      "type": "object"
    },
    "feature_flags": {
      "additionalProperties": true,
      "default": {},
      "title": "Feature Flags",
      "type": "object"
    },
    "is_default": {
      "default": false,
      "title": "Is Default",
      "type": "boolean"
    },
    "is_custom": {
      "default": false,
      "title": "Is Custom",
      "type": "boolean"
    },
    "is_system_profile": {
      "default": false,
      "title": "Is System Profile",
      "type": "boolean"
    },
    "usage_count": {
      "default": 0,
      "minimum": 0,
      "title": "Usage Count",
      "type": "integer"
    },
    "created_at": {
      "format": "date-time",
      "title": "Created At",
      "type": "string"
    },
    "updated_at": {
      "format": "date-time",
      "title": "Updated At",
      "type": "string"
    },
    "last_used": {
      "anyOf": [
        {
          "format": "date-time",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Last Used"
    }
  },
  "required": [
    "id",
    "name",
    "preferred_strategy",
    "ensemble_weights",
    "quality_preference",
    "enable_experimental",
    "confidence_threshold",
    "max_processing_time",
    "fallback_strategy",
    "created_at",
    "updated_at"
  ],
  "title": "UserSettingsProfileSchema",
  "type": "object"
}
```

---

### UserSettingsProfileCreateSchema

**Description:** Schema for creating a new settings profile.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `name` | `<class 'str'>` | ✅ | `PydanticUndefined` |  |  |
| `description` | `typing.Optional[str]` | ❌ | `None` |  |  |
| `preferences` | `<class 'app.schemas.settings.ModelPreferencesSchema'>` | ✅ | `PydanticUndefined` |  |  |
| `copy_from_profile_id` | `typing.Optional[str]` | ❌ | `None` | Copy settings from existing profile |  |

**JSON Schema:**
```json
{
  "$defs": {
    "FallbackStrategy": {
      "description": "Fallback strategy when primary models fail.",
      "enum": [
        "strict",
        "graceful",
        "aggressive"
      ],
      "title": "FallbackStrategy",
      "type": "string"
    },
    "ModelPreferencesSchema": {
      "description": "User's model selection preferences.",
      "properties": {
        "preferred_strategy": {
          "$ref": "#/$defs/ModelSelectionStrategy",
          "default": "auto"
        },
        "ensemble_weights": {
          "additionalProperties": {
            "type": "number"
          },
          "default": {
            "huggingface_ensemble": 0.7,
            "ast_model": 0.25,
            "fallback_classifier": 0.05
          },
          "description": "Weights for ensemble models",
          "title": "Ensemble Weights",
          "type": "object"
        },
        "quality_preference": {
          "$ref": "#/$defs/QualityPreference",
          "default": "balanced"
        },
        "enable_experimental": {
          "default": false,
          "description": "Enable experimental features",
          "title": "Enable Experimental",
          "type": "boolean"
        },
        "confidence_threshold": {
          "default": 0.6,
          "description": "Minimum confidence threshold",
          "maximum": 0.95,
          "minimum": 0.5,
          "title": "Confidence Threshold",
          "type": "number"
        },
        "max_processing_time": {
          "default": 5000,
          "description": "Max processing time in milliseconds",
          "maximum": 10000,
          "minimum": 1000,
          "title": "Max Processing Time",
          "type": "integer"
        },
        "fallback_strategy": {
          "$ref": "#/$defs/FallbackStrategy",
          "default": "graceful"
        },
        "custom_settings": {
          "additionalProperties": true,
          "default": {},
          "description": "Custom user settings",
          "title": "Custom Settings",
          "type": "object"
        }
      },
      "title": "ModelPreferencesSchema",
      "type": "object"
    },
    "ModelSelectionStrategy": {
      "description": "Model selection strategy options.",
      "enum": [
        "auto",
        "performance",
        "quality",
        "custom"
      ],
      "title": "ModelSelectionStrategy",
      "type": "string"
    },
    "QualityPreference": {
      "description": "Quality vs speed preference options.",
      "enum": [
        "fast",
        "balanced",
        "quality"
      ],
      "title": "QualityPreference",
      "type": "string"
    }
  },
  "description": "Schema for creating a new settings profile.",
  "properties": {
    "name": {
      "maxLength": 100,
      "minLength": 1,
      "title": "Name",
      "type": "string"
    },
    "description": {
      "anyOf": [
        {
          "maxLength": 500,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Description"
    },
    "preferences": {
      "$ref": "#/$defs/ModelPreferencesSchema"
    },
    "copy_from_profile_id": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Copy settings from existing profile",
      "title": "Copy From Profile Id"
    }
  },
  "required": [
    "name",
    "preferences"
  ],
  "title": "UserSettingsProfileCreateSchema",
  "type": "object"
}
```

---

### UserSettingsProfileUpdateSchema

**Description:** Schema for updating an existing settings profile.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `name` | `typing.Optional[str]` | ❌ | `None` |  |  |
| `description` | `typing.Optional[str]` | ❌ | `None` |  |  |
| `preferences` | `typing.Optional[app.schemas.settings.ModelPreferencesUpdateSchema]` | ❌ | `None` |  |  |

**JSON Schema:**
```json
{
  "$defs": {
    "FallbackStrategy": {
      "description": "Fallback strategy when primary models fail.",
      "enum": [
        "strict",
        "graceful",
        "aggressive"
      ],
      "title": "FallbackStrategy",
      "type": "string"
    },
    "ModelPreferencesUpdateSchema": {
      "description": "Schema for updating model preferences.",
      "properties": {
        "preferred_strategy": {
          "anyOf": [
            {
              "$ref": "#/$defs/ModelSelectionStrategy"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "ensemble_weights": {
          "anyOf": [
            {
              "additionalProperties": {
                "type": "number"
              },
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Ensemble Weights"
        },
        "quality_preference": {
          "anyOf": [
            {
              "$ref": "#/$defs/QualityPreference"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "enable_experimental": {
          "anyOf": [
            {
              "type": "boolean"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Enable Experimental"
        },
        "confidence_threshold": {
          "anyOf": [
            {
              "maximum": 0.95,
              "minimum": 0.5,
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Confidence Threshold"
        },
        "max_processing_time": {
          "anyOf": [
            {
              "maximum": 10000,
              "minimum": 1000,
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Max Processing Time"
        },
        "fallback_strategy": {
          "anyOf": [
            {
              "$ref": "#/$defs/FallbackStrategy"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "custom_settings": {
          "anyOf": [
            {
              "additionalProperties": true,
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Custom Settings"
        }
      },
      "title": "ModelPreferencesUpdateSchema",
      "type": "object"
    },
    "ModelSelectionStrategy": {
      "description": "Model selection strategy options.",
      "enum": [
        "auto",
        "performance",
        "quality",
        "custom"
      ],
      "title": "ModelSelectionStrategy",
      "type": "string"
    },
    "QualityPreference": {
      "description": "Quality vs speed preference options.",
      "enum": [
        "fast",
        "balanced",
        "quality"
      ],
      "title": "QualityPreference",
      "type": "string"
    }
  },
  "description": "Schema for updating an existing settings profile.",
  "properties": {
    "name": {
      "anyOf": [
        {
          "maxLength": 100,
          "minLength": 1,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Name"
    },
    "description": {
      "anyOf": [
        {
          "maxLength": 500,
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Description"
    },
    "preferences": {
      "anyOf": [
        {
          "$ref": "#/$defs/ModelPreferencesUpdateSchema"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    }
  },
  "title": "UserSettingsProfileUpdateSchema",
  "type": "object"
}
```

---

### AvailableModelInfoSchema

**Description:** Information about an available AI model.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `id` | `<class 'str'>` | ✅ | `PydanticUndefined` |  |  |
| `name` | `<class 'str'>` | ✅ | `PydanticUndefined` |  |  |
| `description` | `<class 'str'>` | ✅ | `PydanticUndefined` |  |  |
| `type` | `<enum 'ModelType'>` | ✅ | `PydanticUndefined` |  |  |
| `performance` | `<class 'app.schemas.settings.ModelPerformanceInfoSchema'>` | ✅ | `PydanticUndefined` |  |  |
| `is_available` | `<class 'bool'>` | ❌ | `True` |  |  |
| `requirements` | `typing.List[str]` | ❌ | `[]` | System requirements |  |
| `version` | `<class 'str'>` | ❌ | `1.0.0` |  |  |
| `provider` | `<class 'str'>` | ❌ | `Matchering` |  |  |

**JSON Schema:**
```json
{
  "$defs": {
    "ModelPerformanceInfoSchema": {
      "description": "Performance information for an AI model.",
      "properties": {
        "average_processing_time": {
          "description": "Average processing time in milliseconds",
          "minimum": 0,
          "title": "Average Processing Time",
          "type": "number"
        },
        "accuracy": {
          "description": "Model accuracy (0.0-1.0)",
          "maximum": 1.0,
          "minimum": 0.0,
          "title": "Accuracy",
          "type": "number"
        },
        "memory_usage": {
          "description": "Memory usage in MB",
          "minimum": 0,
          "title": "Memory Usage",
          "type": "number"
        },
        "gpu_required": {
          "default": false,
          "description": "Whether GPU is required",
          "title": "Gpu Required",
          "type": "boolean"
        },
        "supported_genres": {
          "default": [],
          "description": "List of supported music genres",
          "items": {
            "type": "string"
          },
          "title": "Supported Genres",
          "type": "array"
        }
      },
      "required": [
        "average_processing_time",
        "accuracy",
        "memory_usage"
      ],
      "title": "ModelPerformanceInfoSchema",
      "type": "object"
    },
    "ModelType": {
      "description": "Types of AI models available.",
      "enum": [
        "huggingface",
        "ast",
        "custom"
      ],
      "title": "ModelType",
      "type": "string"
    }
  },
  "description": "Information about an available AI model.",
  "properties": {
    "id": {
      "title": "Id",
      "type": "string"
    },
    "name": {
      "title": "Name",
      "type": "string"
    },
    "description": {
      "title": "Description",
      "type": "string"
    },
    "type": {
      "$ref": "#/$defs/ModelType"
    },
    "performance": {
      "$ref": "#/$defs/ModelPerformanceInfoSchema"
    },
    "is_available": {
      "default": true,
      "title": "Is Available",
      "type": "boolean"
    },
    "requirements": {
      "default": [],
      "description": "System requirements",
      "items": {
        "type": "string"
      },
      "title": "Requirements",
      "type": "array"
    },
    "version": {
      "default": "1.0.0",
      "title": "Version",
      "type": "string"
    },
    "provider": {
      "default": "Matchering",
      "title": "Provider",
      "type": "string"
    }
  },
  "required": [
    "id",
    "name",
    "description",
    "type",
    "performance"
  ],
  "title": "AvailableModelInfoSchema",
  "type": "object"
}
```

---

### ModelPerformanceInfoSchema

**Description:** Performance information for an AI model.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `average_processing_time` | `<class 'float'>` | ✅ | `PydanticUndefined` | Average processing time in milliseconds |  |
| `accuracy` | `<class 'float'>` | ✅ | `PydanticUndefined` | Model accuracy (0.0-1.0) |  |
| `memory_usage` | `<class 'float'>` | ✅ | `PydanticUndefined` | Memory usage in MB |  |
| `gpu_required` | `<class 'bool'>` | ❌ | `False` | Whether GPU is required |  |
| `supported_genres` | `typing.List[str]` | ❌ | `[]` | List of supported music genres |  |

**JSON Schema:**
```json
{
  "description": "Performance information for an AI model.",
  "properties": {
    "average_processing_time": {
      "description": "Average processing time in milliseconds",
      "minimum": 0,
      "title": "Average Processing Time",
      "type": "number"
    },
    "accuracy": {
      "description": "Model accuracy (0.0-1.0)",
      "maximum": 1.0,
      "minimum": 0.0,
      "title": "Accuracy",
      "type": "number"
    },
    "memory_usage": {
      "description": "Memory usage in MB",
      "minimum": 0,
      "title": "Memory Usage",
      "type": "number"
    },
    "gpu_required": {
      "default": false,
      "description": "Whether GPU is required",
      "title": "Gpu Required",
      "type": "boolean"
    },
    "supported_genres": {
      "default": [],
      "description": "List of supported music genres",
      "items": {
        "type": "string"
      },
      "title": "Supported Genres",
      "type": "array"
    }
  },
  "required": [
    "average_processing_time",
    "accuracy",
    "memory_usage"
  ],
  "title": "ModelPerformanceInfoSchema",
  "type": "object"
}
```

---

### SettingsConfigResponse

**Description:** Complete settings configuration response.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `current_profile` | `<class 'app.schemas.settings.UserSettingsProfileSchema'>` | ✅ | `PydanticUndefined` |  |  |
| `available_profiles` | `typing.List[app.schemas.settings.UserSettingsProfileSchema]` | ✅ | `PydanticUndefined` |  |  |
| `available_models` | `typing.List[app.schemas.settings.AvailableModelInfoSchema]` | ✅ | `PydanticUndefined` |  |  |
| `system_defaults` | `<class 'app.schemas.settings.ModelPreferencesSchema'>` | ✅ | `PydanticUndefined` |  |  |
| `feature_flags` | `typing.Dict[str, bool]` | ❌ | `{}` |  |  |

**JSON Schema:**
```json
{
  "$defs": {
    "AvailableModelInfoSchema": {
      "description": "Information about an available AI model.",
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "name": {
          "title": "Name",
          "type": "string"
        },
        "description": {
          "title": "Description",
          "type": "string"
        },
        "type": {
          "$ref": "#/$defs/ModelType"
        },
        "performance": {
          "$ref": "#/$defs/ModelPerformanceInfoSchema"
        },
        "is_available": {
          "default": true,
          "title": "Is Available",
          "type": "boolean"
        },
        "requirements": {
          "default": [],
          "description": "System requirements",
          "items": {
            "type": "string"
          },
          "title": "Requirements",
          "type": "array"
        },
        "version": {
          "default": "1.0.0",
          "title": "Version",
          "type": "string"
        },
        "provider": {
          "default": "Matchering",
          "title": "Provider",
          "type": "string"
        }
      },
      "required": [
        "id",
        "name",
        "description",
        "type",
        "performance"
      ],
      "title": "AvailableModelInfoSchema",
      "type": "object"
    },
    "FallbackStrategy": {
      "description": "Fallback strategy when primary models fail.",
      "enum": [
        "strict",
        "graceful",
        "aggressive"
      ],
      "title": "FallbackStrategy",
      "type": "string"
    },
    "ModelPerformanceInfoSchema": {
      "description": "Performance information for an AI model.",
      "properties": {
        "average_processing_time": {
          "description": "Average processing time in milliseconds",
          "minimum": 0,
          "title": "Average Processing Time",
          "type": "number"
        },
        "accuracy": {
          "description": "Model accuracy (0.0-1.0)",
          "maximum": 1.0,
          "minimum": 0.0,
          "title": "Accuracy",
          "type": "number"
        },
        "memory_usage": {
          "description": "Memory usage in MB",
          "minimum": 0,
          "title": "Memory Usage",
          "type": "number"
        },
        "gpu_required": {
          "default": false,
          "description": "Whether GPU is required",
          "title": "Gpu Required",
          "type": "boolean"
        },
        "supported_genres": {
          "default": [],
          "description": "List of supported music genres",
          "items": {
            "type": "string"
          },
          "title": "Supported Genres",
          "type": "array"
        }
      },
      "required": [
        "average_processing_time",
        "accuracy",
        "memory_usage"
      ],
      "title": "ModelPerformanceInfoSchema",
      "type": "object"
    },
    "ModelPreferencesSchema": {
      "description": "User's model selection preferences.",
      "properties": {
        "preferred_strategy": {
          "$ref": "#/$defs/ModelSelectionStrategy",
          "default": "auto"
        },
        "ensemble_weights": {
          "additionalProperties": {
            "type": "number"
          },
          "default": {
            "huggingface_ensemble": 0.7,
            "ast_model": 0.25,
            "fallback_classifier": 0.05
          },
          "description": "Weights for ensemble models",
          "title": "Ensemble Weights",
          "type": "object"
        },
        "quality_preference": {
          "$ref": "#/$defs/QualityPreference",
          "default": "balanced"
        },
        "enable_experimental": {
          "default": false,
          "description": "Enable experimental features",
          "title": "Enable Experimental",
          "type": "boolean"
        },
        "confidence_threshold": {
          "default": 0.6,
          "description": "Minimum confidence threshold",
          "maximum": 0.95,
          "minimum": 0.5,
          "title": "Confidence Threshold",
          "type": "number"
        },
        "max_processing_time": {
          "default": 5000,
          "description": "Max processing time in milliseconds",
          "maximum": 10000,
          "minimum": 1000,
          "title": "Max Processing Time",
          "type": "integer"
        },
        "fallback_strategy": {
          "$ref": "#/$defs/FallbackStrategy",
          "default": "graceful"
        },
        "custom_settings": {
          "additionalProperties": true,
          "default": {},
          "description": "Custom user settings",
          "title": "Custom Settings",
          "type": "object"
        }
      },
      "title": "ModelPreferencesSchema",
      "type": "object"
    },
    "ModelSelectionStrategy": {
      "description": "Model selection strategy options.",
      "enum": [
        "auto",
        "performance",
        "quality",
        "custom"
      ],
      "title": "ModelSelectionStrategy",
      "type": "string"
    },
    "ModelType": {
      "description": "Types of AI models available.",
      "enum": [
        "huggingface",
        "ast",
        "custom"
      ],
      "title": "ModelType",
      "type": "string"
    },
    "QualityPreference": {
      "description": "Quality vs speed preference options.",
      "enum": [
        "fast",
        "balanced",
        "quality"
      ],
      "title": "QualityPreference",
      "type": "string"
    },
    "UserSettingsProfileSchema": {
      "description": "Complete user settings profile.",
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "name": {
          "maxLength": 100,
          "minLength": 1,
          "title": "Name",
          "type": "string"
        },
        "description": {
          "anyOf": [
            {
              "maxLength": 500,
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Description"
        },
        "preferred_strategy": {
          "$ref": "#/$defs/ModelSelectionStrategy"
        },
        "ensemble_weights": {
          "additionalProperties": {
            "type": "number"
          },
          "title": "Ensemble Weights",
          "type": "object"
        },
        "quality_preference": {
          "$ref": "#/$defs/QualityPreference"
        },
        "enable_experimental": {
          "title": "Enable Experimental",
          "type": "boolean"
        },
        "confidence_threshold": {
          "title": "Confidence Threshold",
          "type": "number"
        },
        "max_processing_time": {
          "title": "Max Processing Time",
          "type": "integer"
        },
        "fallback_strategy": {
          "$ref": "#/$defs/FallbackStrategy"
        },
        "advanced_settings": {
          "additionalProperties": true,
          "default": {},
          "title": "Advanced Settings",
          "type": "object"
        },
        "feature_flags": {
          "additionalProperties": true,
          "default": {},
          "title": "Feature Flags",
          "type": "object"
        },
        "is_default": {
          "default": false,
          "title": "Is Default",
          "type": "boolean"
        },
        "is_custom": {
          "default": false,
          "title": "Is Custom",
          "type": "boolean"
        },
        "is_system_profile": {
          "default": false,
          "title": "Is System Profile",
          "type": "boolean"
        },
        "usage_count": {
          "default": 0,
          "minimum": 0,
          "title": "Usage Count",
          "type": "integer"
        },
        "created_at": {
          "format": "date-time",
          "title": "Created At",
          "type": "string"
        },
        "updated_at": {
          "format": "date-time",
          "title": "Updated At",
          "type": "string"
        },
        "last_used": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Last Used"
        }
      },
      "required": [
        "id",
        "name",
        "preferred_strategy",
        "ensemble_weights",
        "quality_preference",
        "enable_experimental",
        "confidence_threshold",
        "max_processing_time",
        "fallback_strategy",
        "created_at",
        "updated_at"
      ],
      "title": "UserSettingsProfileSchema",
      "type": "object"
    }
  },
  "description": "Complete settings configuration response.",
  "properties": {
    "current_profile": {
      "$ref": "#/$defs/UserSettingsProfileSchema"
    },
    "available_profiles": {
      "items": {
        "$ref": "#/$defs/UserSettingsProfileSchema"
      },
      "title": "Available Profiles",
      "type": "array"
    },
    "available_models": {
      "items": {
        "$ref": "#/$defs/AvailableModelInfoSchema"
      },
      "title": "Available Models",
      "type": "array"
    },
    "system_defaults": {
      "$ref": "#/$defs/ModelPreferencesSchema"
    },
    "feature_flags": {
      "additionalProperties": {
        "type": "boolean"
      },
      "default": {},
      "title": "Feature Flags",
      "type": "object"
    }
  },
  "required": [
    "current_profile",
    "available_profiles",
    "available_models",
    "system_defaults"
  ],
  "title": "SettingsConfigResponse",
  "type": "object"
}
```

---

### SettingsUpdateResponse

**Description:** Response after updating settings.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `success` | `<class 'bool'>` | ❌ | `True` |  |  |
| `profile` | `<class 'app.schemas.settings.UserSettingsProfileSchema'>` | ✅ | `PydanticUndefined` |  |  |
| `cache_invalidated` | `<class 'bool'>` | ❌ | `False` |  |  |
| `message` | `<class 'str'>` | ❌ | `Settings updated successfully` |  |  |

**JSON Schema:**
```json
{
  "$defs": {
    "FallbackStrategy": {
      "description": "Fallback strategy when primary models fail.",
      "enum": [
        "strict",
        "graceful",
        "aggressive"
      ],
      "title": "FallbackStrategy",
      "type": "string"
    },
    "ModelSelectionStrategy": {
      "description": "Model selection strategy options.",
      "enum": [
        "auto",
        "performance",
        "quality",
        "custom"
      ],
      "title": "ModelSelectionStrategy",
      "type": "string"
    },
    "QualityPreference": {
      "description": "Quality vs speed preference options.",
      "enum": [
        "fast",
        "balanced",
        "quality"
      ],
      "title": "QualityPreference",
      "type": "string"
    },
    "UserSettingsProfileSchema": {
      "description": "Complete user settings profile.",
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "name": {
          "maxLength": 100,
          "minLength": 1,
          "title": "Name",
          "type": "string"
        },
        "description": {
          "anyOf": [
            {
              "maxLength": 500,
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Description"
        },
        "preferred_strategy": {
          "$ref": "#/$defs/ModelSelectionStrategy"
        },
        "ensemble_weights": {
          "additionalProperties": {
            "type": "number"
          },
          "title": "Ensemble Weights",
          "type": "object"
        },
        "quality_preference": {
          "$ref": "#/$defs/QualityPreference"
        },
        "enable_experimental": {
          "title": "Enable Experimental",
          "type": "boolean"
        },
        "confidence_threshold": {
          "title": "Confidence Threshold",
          "type": "number"
        },
        "max_processing_time": {
          "title": "Max Processing Time",
          "type": "integer"
        },
        "fallback_strategy": {
          "$ref": "#/$defs/FallbackStrategy"
        },
        "advanced_settings": {
          "additionalProperties": true,
          "default": {},
          "title": "Advanced Settings",
          "type": "object"
        },
        "feature_flags": {
          "additionalProperties": true,
          "default": {},
          "title": "Feature Flags",
          "type": "object"
        },
        "is_default": {
          "default": false,
          "title": "Is Default",
          "type": "boolean"
        },
        "is_custom": {
          "default": false,
          "title": "Is Custom",
          "type": "boolean"
        },
        "is_system_profile": {
          "default": false,
          "title": "Is System Profile",
          "type": "boolean"
        },
        "usage_count": {
          "default": 0,
          "minimum": 0,
          "title": "Usage Count",
          "type": "integer"
        },
        "created_at": {
          "format": "date-time",
          "title": "Created At",
          "type": "string"
        },
        "updated_at": {
          "format": "date-time",
          "title": "Updated At",
          "type": "string"
        },
        "last_used": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Last Used"
        }
      },
      "required": [
        "id",
        "name",
        "preferred_strategy",
        "ensemble_weights",
        "quality_preference",
        "enable_experimental",
        "confidence_threshold",
        "max_processing_time",
        "fallback_strategy",
        "created_at",
        "updated_at"
      ],
      "title": "UserSettingsProfileSchema",
      "type": "object"
    }
  },
  "description": "Response after updating settings.",
  "properties": {
    "success": {
      "default": true,
      "title": "Success",
      "type": "boolean"
    },
    "profile": {
      "$ref": "#/$defs/UserSettingsProfileSchema"
    },
    "cache_invalidated": {
      "default": false,
      "title": "Cache Invalidated",
      "type": "boolean"
    },
    "message": {
      "default": "Settings updated successfully",
      "title": "Message",
      "type": "string"
    }
  },
  "required": [
    "profile"
  ],
  "title": "SettingsUpdateResponse",
  "type": "object"
}
```

---

### ProfileSelectionResponse

**Description:** Response after selecting a profile.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `success` | `<class 'bool'>` | ❌ | `True` |  |  |
| `active_profile` | `<class 'app.schemas.settings.UserSettingsProfileSchema'>` | ✅ | `PydanticUndefined` |  |  |
| `previous_profile_id` | `typing.Optional[str]` | ❌ | `None` |  |  |
| `message` | `<class 'str'>` | ❌ | `Profile selected successfully` |  |  |

**JSON Schema:**
```json
{
  "$defs": {
    "FallbackStrategy": {
      "description": "Fallback strategy when primary models fail.",
      "enum": [
        "strict",
        "graceful",
        "aggressive"
      ],
      "title": "FallbackStrategy",
      "type": "string"
    },
    "ModelSelectionStrategy": {
      "description": "Model selection strategy options.",
      "enum": [
        "auto",
        "performance",
        "quality",
        "custom"
      ],
      "title": "ModelSelectionStrategy",
      "type": "string"
    },
    "QualityPreference": {
      "description": "Quality vs speed preference options.",
      "enum": [
        "fast",
        "balanced",
        "quality"
      ],
      "title": "QualityPreference",
      "type": "string"
    },
    "UserSettingsProfileSchema": {
      "description": "Complete user settings profile.",
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "name": {
          "maxLength": 100,
          "minLength": 1,
          "title": "Name",
          "type": "string"
        },
        "description": {
          "anyOf": [
            {
              "maxLength": 500,
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Description"
        },
        "preferred_strategy": {
          "$ref": "#/$defs/ModelSelectionStrategy"
        },
        "ensemble_weights": {
          "additionalProperties": {
            "type": "number"
          },
          "title": "Ensemble Weights",
          "type": "object"
        },
        "quality_preference": {
          "$ref": "#/$defs/QualityPreference"
        },
        "enable_experimental": {
          "title": "Enable Experimental",
          "type": "boolean"
        },
        "confidence_threshold": {
          "title": "Confidence Threshold",
          "type": "number"
        },
        "max_processing_time": {
          "title": "Max Processing Time",
          "type": "integer"
        },
        "fallback_strategy": {
          "$ref": "#/$defs/FallbackStrategy"
        },
        "advanced_settings": {
          "additionalProperties": true,
          "default": {},
          "title": "Advanced Settings",
          "type": "object"
        },
        "feature_flags": {
          "additionalProperties": true,
          "default": {},
          "title": "Feature Flags",
          "type": "object"
        },
        "is_default": {
          "default": false,
          "title": "Is Default",
          "type": "boolean"
        },
        "is_custom": {
          "default": false,
          "title": "Is Custom",
          "type": "boolean"
        },
        "is_system_profile": {
          "default": false,
          "title": "Is System Profile",
          "type": "boolean"
        },
        "usage_count": {
          "default": 0,
          "minimum": 0,
          "title": "Usage Count",
          "type": "integer"
        },
        "created_at": {
          "format": "date-time",
          "title": "Created At",
          "type": "string"
        },
        "updated_at": {
          "format": "date-time",
          "title": "Updated At",
          "type": "string"
        },
        "last_used": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Last Used"
        }
      },
      "required": [
        "id",
        "name",
        "preferred_strategy",
        "ensemble_weights",
        "quality_preference",
        "enable_experimental",
        "confidence_threshold",
        "max_processing_time",
        "fallback_strategy",
        "created_at",
        "updated_at"
      ],
      "title": "UserSettingsProfileSchema",
      "type": "object"
    }
  },
  "description": "Response after selecting a profile.",
  "properties": {
    "success": {
      "default": true,
      "title": "Success",
      "type": "boolean"
    },
    "active_profile": {
      "$ref": "#/$defs/UserSettingsProfileSchema"
    },
    "previous_profile_id": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Previous Profile Id"
    },
    "message": {
      "default": "Profile selected successfully",
      "title": "Message",
      "type": "string"
    }
  },
  "required": [
    "active_profile"
  ],
  "title": "ProfileSelectionResponse",
  "type": "object"
}
```

---

### UserSettingsAnalyticsSchema

**Description:** User settings usage analytics.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `total_processing_jobs` | `<class 'int'>` | ❌ | `0` |  |  |
| `average_processing_time` | `<class 'float'>` | ❌ | `0.0` |  |  |
| `most_used_model` | `typing.Optional[str]` | ❌ | `None` |  |  |
| `model_usage_distribution` | `typing.Dict[str, int]` | ❌ | `{}` |  |  |
| `quality_ratings` | `typing.Dict[str, float]` | ❌ | `{}` |  |  |
| `performance_trends` | `typing.Dict[str, typing.List[float]]` | ❌ | `{}` |  |  |
| `period_days` | `<class 'int'>` | ❌ | `30` |  |  |

**JSON Schema:**
```json
{
  "description": "User settings usage analytics.",
  "properties": {
    "total_processing_jobs": {
      "default": 0,
      "minimum": 0,
      "title": "Total Processing Jobs",
      "type": "integer"
    },
    "average_processing_time": {
      "default": 0.0,
      "minimum": 0.0,
      "title": "Average Processing Time",
      "type": "number"
    },
    "most_used_model": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Most Used Model"
    },
    "model_usage_distribution": {
      "additionalProperties": {
        "type": "integer"
      },
      "default": {},
      "title": "Model Usage Distribution",
      "type": "object"
    },
    "quality_ratings": {
      "additionalProperties": {
        "type": "number"
      },
      "default": {},
      "title": "Quality Ratings",
      "type": "object"
    },
    "performance_trends": {
      "additionalProperties": {
        "items": {
          "type": "number"
        },
        "type": "array"
      },
      "default": {},
      "title": "Performance Trends",
      "type": "object"
    },
    "period_days": {
      "default": 30,
      "maximum": 365,
      "minimum": 1,
      "title": "Period Days",
      "type": "integer"
    }
  },
  "title": "UserSettingsAnalyticsSchema",
  "type": "object"
}
```

---

### SystemStatusResponse

**Description:** System status for settings service.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `available_models_count` | `<class 'int'>` | ✅ | `PydanticUndefined` |  |  |
| `active_users_count` | `<class 'int'>` | ✅ | `PydanticUndefined` |  |  |
| `cache_hit_rate` | `<class 'float'>` | ✅ | `PydanticUndefined` |  |  |
| `average_response_time` | `<class 'float'>` | ✅ | `PydanticUndefined` |  |  |
| `feature_flags` | `typing.Dict[str, bool]` | ✅ | `PydanticUndefined` |  |  |
| `celery_status` | `<class 'app.schemas.settings.CeleryStatusSchema'>` | ✅ | `PydanticUndefined` | Celery worker and task queue status |  |
| `last_updated` | `<class 'datetime.datetime'>` | ✅ | `PydanticUndefined` |  |  |

**JSON Schema:**
```json
{
  "$defs": {
    "CeleryStatusSchema": {
      "description": "Overall Celery system status.",
      "properties": {
        "total_workers": {
          "description": "Total number of workers",
          "minimum": 0,
          "title": "Total Workers",
          "type": "integer"
        },
        "active_workers": {
          "description": "Number of active workers",
          "minimum": 0,
          "title": "Active Workers",
          "type": "integer"
        },
        "offline_workers": {
          "description": "Number of offline workers",
          "minimum": 0,
          "title": "Offline Workers",
          "type": "integer"
        },
        "pending_tasks": {
          "description": "Number of pending tasks in all queues",
          "minimum": 0,
          "title": "Pending Tasks",
          "type": "integer"
        },
        "active_tasks": {
          "description": "Number of currently executing tasks",
          "minimum": 0,
          "title": "Active Tasks",
          "type": "integer"
        },
        "failed_tasks_recent": {
          "description": "Number of failed tasks in last hour",
          "minimum": 0,
          "title": "Failed Tasks Recent",
          "type": "integer"
        },
        "queue_lengths": {
          "additionalProperties": {
            "type": "integer"
          },
          "default": {},
          "description": "Length of each queue",
          "title": "Queue Lengths",
          "type": "object"
        },
        "workers": {
          "default": [],
          "description": "Individual worker statuses",
          "items": {
            "$ref": "#/$defs/CeleryWorkerStatusSchema"
          },
          "title": "Workers",
          "type": "array"
        },
        "broker_status": {
          "description": "Redis broker connection status",
          "enum": [
            "connected",
            "disconnected",
            "unknown"
          ],
          "title": "Broker Status",
          "type": "string"
        },
        "last_updated": {
          "description": "When this status was last updated",
          "format": "date-time",
          "title": "Last Updated",
          "type": "string"
        }
      },
      "required": [
        "total_workers",
        "active_workers",
        "offline_workers",
        "pending_tasks",
        "active_tasks",
        "failed_tasks_recent",
        "broker_status",
        "last_updated"
      ],
      "title": "CeleryStatusSchema",
      "type": "object"
    },
    "CeleryWorkerStatusSchema": {
      "description": "Celery worker status information.",
      "properties": {
        "worker_id": {
          "description": "Unique worker identifier",
          "title": "Worker Id",
          "type": "string"
        },
        "hostname": {
          "description": "Worker hostname",
          "title": "Hostname",
          "type": "string"
        },
        "status": {
          "description": "Worker status",
          "enum": [
            "online",
            "offline",
            "unknown"
          ],
          "title": "Status",
          "type": "string"
        },
        "active_tasks": {
          "description": "Number of currently active tasks",
          "minimum": 0,
          "title": "Active Tasks",
          "type": "integer"
        },
        "processed_tasks": {
          "description": "Total number of processed tasks",
          "minimum": 0,
          "title": "Processed Tasks",
          "type": "integer"
        },
        "load_average": {
          "default": [],
          "description": "System load average [1min, 5min, 15min]",
          "items": {
            "type": "number"
          },
          "title": "Load Average",
          "type": "array"
        },
        "memory_usage": {
          "additionalProperties": true,
          "default": {},
          "description": "Memory usage statistics",
          "title": "Memory Usage",
          "type": "object"
        },
        "queues": {
          "default": [],
          "description": "Queues this worker is listening to",
          "items": {
            "type": "string"
          },
          "title": "Queues",
          "type": "array"
        },
        "last_heartbeat": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Last heartbeat timestamp",
          "title": "Last Heartbeat"
        }
      },
      "required": [
        "worker_id",
        "hostname",
        "status",
        "active_tasks",
        "processed_tasks"
      ],
      "title": "CeleryWorkerStatusSchema",
      "type": "object"
    }
  },
  "description": "System status for settings service.",
  "properties": {
    "available_models_count": {
      "title": "Available Models Count",
      "type": "integer"
    },
    "active_users_count": {
      "title": "Active Users Count",
      "type": "integer"
    },
    "cache_hit_rate": {
      "maximum": 1.0,
      "minimum": 0.0,
      "title": "Cache Hit Rate",
      "type": "number"
    },
    "average_response_time": {
      "minimum": 0.0,
      "title": "Average Response Time",
      "type": "number"
    },
    "feature_flags": {
      "additionalProperties": {
        "type": "boolean"
      },
      "title": "Feature Flags",
      "type": "object"
    },
    "celery_status": {
      "$ref": "#/$defs/CeleryStatusSchema",
      "description": "Celery worker and task queue status"
    },
    "last_updated": {
      "format": "date-time",
      "title": "Last Updated",
      "type": "string"
    }
  },
  "required": [
    "available_models_count",
    "active_users_count",
    "cache_hit_rate",
    "average_response_time",
    "feature_flags",
    "celery_status",
    "last_updated"
  ],
  "title": "SystemStatusResponse",
  "type": "object"
}
```

---

### ProcessingJobCreate

**Description:** Processing job creation request.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `input_file_id` | `<class 'uuid.UUID'>` | ✅ | `PydanticUndefined` | Input audio file ID |  |
| `reference_file_id` | `typing.Optional[uuid.UUID]` | ❌ | `None` | Reference file ID (for reference mastering) |  |
| `processing_mode` | `<class 'str'>` | ✅ | `PydanticUndefined` | Processing mode (auto, reference, hybrid) |  |
| `settings` | `typing.Dict[str, typing.Any]` | ❌ | `PydanticUndefined` | Processing settings |  |
| `priority` | `<class 'int'>` | ❌ | `5` | Job priority (1=highest, 10=lowest) |  |

**JSON Schema:**
```json
{
  "description": "Processing job creation request.",
  "properties": {
    "input_file_id": {
      "description": "Input audio file ID",
      "format": "uuid",
      "title": "Input File Id",
      "type": "string"
    },
    "reference_file_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Reference file ID (for reference mastering)",
      "title": "Reference File Id"
    },
    "processing_mode": {
      "description": "Processing mode (auto, reference, hybrid)",
      "title": "Processing Mode",
      "type": "string"
    },
    "settings": {
      "additionalProperties": true,
      "description": "Processing settings",
      "title": "Settings",
      "type": "object"
    },
    "priority": {
      "default": 5,
      "description": "Job priority (1=highest, 10=lowest)",
      "maximum": 10,
      "minimum": 1,
      "title": "Priority",
      "type": "integer"
    }
  },
  "required": [
    "input_file_id",
    "processing_mode"
  ],
  "title": "ProcessingJobCreate",
  "type": "object"
}
```

---

### ProcessingJobResponse

**Description:** Processing job response model.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `id` | `<class 'uuid.UUID'>` | ✅ | `PydanticUndefined` | Job identifier |  |
| `input_file_id` | `<class 'uuid.UUID'>` | ✅ | `PydanticUndefined` | Input file ID |  |
| `reference_file_id` | `typing.Optional[uuid.UUID]` | ❌ | `None` | Reference file ID |  |
| `output_file_path` | `typing.Optional[str]` | ❌ | `None` | Output file path |  |
| `processing_mode` | `<class 'str'>` | ✅ | `PydanticUndefined` | Processing mode |  |
| `settings` | `typing.Dict[str, typing.Any]` | ✅ | `PydanticUndefined` | Processing settings |  |
| `status` | `<class 'str'>` | ✅ | `PydanticUndefined` | Job status |  |
| `queue_position` | `typing.Optional[int]` | ❌ | `None` | Position in queue |  |
| `priority` | `<class 'int'>` | ✅ | `PydanticUndefined` | Job priority |  |
| `created_at` | `<class 'datetime.datetime'>` | ✅ | `PydanticUndefined` | Job creation time |  |
| `started_at` | `typing.Optional[datetime.datetime]` | ❌ | `None` | Job start time |  |
| `completed_at` | `typing.Optional[datetime.datetime]` | ❌ | `None` | Job completion time |  |
| `current_stage` | `typing.Optional[str]` | ❌ | `None` | Current processing stage |  |
| `progress_percentage` | `<class 'float'>` | ✅ | `PydanticUndefined` | Overall progress percentage |  |
| `estimated_completion` | `typing.Optional[datetime.datetime]` | ❌ | `None` | Estimated completion time |  |
| `result_metadata` | `typing.Optional[typing.Dict[str, typing.Any]]` | ❌ | `None` | Processing results |  |
| `error_message` | `typing.Optional[str]` | ❌ | `None` | Error message if failed |  |
| `error_code` | `typing.Optional[str]` | ❌ | `None` | Error code if failed |  |
| `retry_count` | `<class 'int'>` | ✅ | `PydanticUndefined` | Number of retry attempts |  |
| `processing_duration` | `typing.Optional[float]` | ❌ | `None` | Processing time in seconds |  |
| `cpu_time` | `typing.Optional[float]` | ❌ | `None` | CPU time used |  |
| `memory_peak` | `typing.Optional[int]` | ❌ | `None` | Peak memory usage in bytes |  |

**JSON Schema:**
```json
{
  "description": "Processing job response model.",
  "properties": {
    "id": {
      "description": "Job identifier",
      "format": "uuid",
      "title": "Id",
      "type": "string"
    },
    "input_file_id": {
      "description": "Input file ID",
      "format": "uuid",
      "title": "Input File Id",
      "type": "string"
    },
    "reference_file_id": {
      "anyOf": [
        {
          "format": "uuid",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Reference file ID",
      "title": "Reference File Id"
    },
    "output_file_path": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Output file path",
      "title": "Output File Path"
    },
    "processing_mode": {
      "description": "Processing mode",
      "title": "Processing Mode",
      "type": "string"
    },
    "settings": {
      "additionalProperties": true,
      "description": "Processing settings",
      "title": "Settings",
      "type": "object"
    },
    "status": {
      "description": "Job status",
      "title": "Status",
      "type": "string"
    },
    "queue_position": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Position in queue",
      "title": "Queue Position"
    },
    "priority": {
      "description": "Job priority",
      "title": "Priority",
      "type": "integer"
    },
    "created_at": {
      "description": "Job creation time",
      "format": "date-time",
      "title": "Created At",
      "type": "string"
    },
    "started_at": {
      "anyOf": [
        {
          "format": "date-time",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Job start time",
      "title": "Started At"
    },
    "completed_at": {
      "anyOf": [
        {
          "format": "date-time",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Job completion time",
      "title": "Completed At"
    },
    "current_stage": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Current processing stage",
      "title": "Current Stage"
    },
    "progress_percentage": {
      "description": "Overall progress percentage",
      "title": "Progress Percentage",
      "type": "number"
    },
    "estimated_completion": {
      "anyOf": [
        {
          "format": "date-time",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Estimated completion time",
      "title": "Estimated Completion"
    },
    "result_metadata": {
      "anyOf": [
        {
          "additionalProperties": true,
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Processing results",
      "title": "Result Metadata"
    },
    "error_message": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Error message if failed",
      "title": "Error Message"
    },
    "error_code": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Error code if failed",
      "title": "Error Code"
    },
    "retry_count": {
      "description": "Number of retry attempts",
      "title": "Retry Count",
      "type": "integer"
    },
    "processing_duration": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Processing time in seconds",
      "title": "Processing Duration"
    },
    "cpu_time": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "CPU time used",
      "title": "Cpu Time"
    },
    "memory_peak": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Peak memory usage in bytes",
      "title": "Memory Peak"
    }
  },
  "required": [
    "id",
    "input_file_id",
    "processing_mode",
    "settings",
    "status",
    "priority",
    "created_at",
    "progress_percentage",
    "retry_count"
  ],
  "title": "ProcessingJobResponse",
  "type": "object"
}
```

---

### ProcessingJobListResponse

**Description:** Processing job list response model.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `jobs` | `typing.List[app.schemas.processing.ProcessingJobResponse]` | ✅ | `PydanticUndefined` | List of processing jobs |  |
| `pagination` | `<class 'app.schemas.common.PaginationInfo'>` | ✅ | `PydanticUndefined` | Pagination information |  |

**JSON Schema:**
```json
{
  "$defs": {
    "PaginationInfo": {
      "description": "Pagination information in responses.",
      "properties": {
        "total": {
          "description": "Total number of items",
          "minimum": 0,
          "title": "Total",
          "type": "integer"
        },
        "skip": {
          "description": "Number of items skipped",
          "minimum": 0,
          "title": "Skip",
          "type": "integer"
        },
        "limit": {
          "description": "Maximum items returned",
          "minimum": 1,
          "title": "Limit",
          "type": "integer"
        },
        "has_more": {
          "description": "Whether there are more items available",
          "title": "Has More",
          "type": "boolean"
        }
      },
      "required": [
        "total",
        "skip",
        "limit",
        "has_more"
      ],
      "title": "PaginationInfo",
      "type": "object"
    },
    "ProcessingJobResponse": {
      "description": "Processing job response model.",
      "properties": {
        "id": {
          "description": "Job identifier",
          "format": "uuid",
          "title": "Id",
          "type": "string"
        },
        "input_file_id": {
          "description": "Input file ID",
          "format": "uuid",
          "title": "Input File Id",
          "type": "string"
        },
        "reference_file_id": {
          "anyOf": [
            {
              "format": "uuid",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Reference file ID",
          "title": "Reference File Id"
        },
        "output_file_path": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Output file path",
          "title": "Output File Path"
        },
        "processing_mode": {
          "description": "Processing mode",
          "title": "Processing Mode",
          "type": "string"
        },
        "settings": {
          "additionalProperties": true,
          "description": "Processing settings",
          "title": "Settings",
          "type": "object"
        },
        "status": {
          "description": "Job status",
          "title": "Status",
          "type": "string"
        },
        "queue_position": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Position in queue",
          "title": "Queue Position"
        },
        "priority": {
          "description": "Job priority",
          "title": "Priority",
          "type": "integer"
        },
        "created_at": {
          "description": "Job creation time",
          "format": "date-time",
          "title": "Created At",
          "type": "string"
        },
        "started_at": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Job start time",
          "title": "Started At"
        },
        "completed_at": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Job completion time",
          "title": "Completed At"
        },
        "current_stage": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Current processing stage",
          "title": "Current Stage"
        },
        "progress_percentage": {
          "description": "Overall progress percentage",
          "title": "Progress Percentage",
          "type": "number"
        },
        "estimated_completion": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Estimated completion time",
          "title": "Estimated Completion"
        },
        "result_metadata": {
          "anyOf": [
            {
              "additionalProperties": true,
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Processing results",
          "title": "Result Metadata"
        },
        "error_message": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Error message if failed",
          "title": "Error Message"
        },
        "error_code": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Error code if failed",
          "title": "Error Code"
        },
        "retry_count": {
          "description": "Number of retry attempts",
          "title": "Retry Count",
          "type": "integer"
        },
        "processing_duration": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Processing time in seconds",
          "title": "Processing Duration"
        },
        "cpu_time": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "CPU time used",
          "title": "Cpu Time"
        },
        "memory_peak": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Peak memory usage in bytes",
          "title": "Memory Peak"
        }
      },
      "required": [
        "id",
        "input_file_id",
        "processing_mode",
        "settings",
        "status",
        "priority",
        "created_at",
        "progress_percentage",
        "retry_count"
      ],
      "title": "ProcessingJobResponse",
      "type": "object"
    }
  },
  "description": "Processing job list response model.",
  "properties": {
    "jobs": {
      "description": "List of processing jobs",
      "items": {
        "$ref": "#/$defs/ProcessingJobResponse"
      },
      "title": "Jobs",
      "type": "array"
    },
    "pagination": {
      "$ref": "#/$defs/PaginationInfo",
      "description": "Pagination information"
    }
  },
  "required": [
    "jobs",
    "pagination"
  ],
  "title": "ProcessingJobListResponse",
  "type": "object"
}
```

---

### ProcessingJobDetailResponse

**Description:** Detailed processing job response with progress history.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `job` | `<class 'app.schemas.processing.ProcessingJobResponse'>` | ✅ | `PydanticUndefined` | Job information |  |
| `progress_history` | `typing.List[app.schemas.processing.JobProgressResponse]` | ✅ | `PydanticUndefined` | Progress history |  |
| `input_file` | `typing.Optional[typing.Dict[str, typing.Any]]` | ❌ | `None` | Input file information |  |
| `reference_file` | `typing.Optional[typing.Dict[str, typing.Any]]` | ❌ | `None` | Reference file information |  |
| `output_file` | `typing.Optional[typing.Dict[str, typing.Any]]` | ❌ | `None` | Output file information |  |

**JSON Schema:**
```json
{
  "$defs": {
    "JobProgressResponse": {
      "description": "Job progress response model.",
      "properties": {
        "id": {
          "description": "Progress entry ID",
          "format": "uuid",
          "title": "Id",
          "type": "string"
        },
        "job_id": {
          "description": "Associated job ID",
          "format": "uuid",
          "title": "Job Id",
          "type": "string"
        },
        "stage": {
          "description": "Processing stage",
          "title": "Stage",
          "type": "string"
        },
        "progress_percentage": {
          "description": "Stage progress percentage",
          "title": "Progress Percentage",
          "type": "number"
        },
        "message": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Progress message",
          "title": "Message"
        },
        "timestamp": {
          "description": "Progress timestamp",
          "format": "date-time",
          "title": "Timestamp",
          "type": "string"
        },
        "stage_started_at": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Stage start time",
          "title": "Stage Started At"
        },
        "stage_duration": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Stage duration in seconds",
          "title": "Stage Duration"
        },
        "details": {
          "anyOf": [
            {
              "additionalProperties": true,
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Additional details",
          "title": "Details"
        },
        "warnings": {
          "anyOf": [
            {
              "additionalProperties": true,
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Stage warnings",
          "title": "Warnings"
        }
      },
      "required": [
        "id",
        "job_id",
        "stage",
        "progress_percentage",
        "timestamp"
      ],
      "title": "JobProgressResponse",
      "type": "object"
    },
    "ProcessingJobResponse": {
      "description": "Processing job response model.",
      "properties": {
        "id": {
          "description": "Job identifier",
          "format": "uuid",
          "title": "Id",
          "type": "string"
        },
        "input_file_id": {
          "description": "Input file ID",
          "format": "uuid",
          "title": "Input File Id",
          "type": "string"
        },
        "reference_file_id": {
          "anyOf": [
            {
              "format": "uuid",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Reference file ID",
          "title": "Reference File Id"
        },
        "output_file_path": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Output file path",
          "title": "Output File Path"
        },
        "processing_mode": {
          "description": "Processing mode",
          "title": "Processing Mode",
          "type": "string"
        },
        "settings": {
          "additionalProperties": true,
          "description": "Processing settings",
          "title": "Settings",
          "type": "object"
        },
        "status": {
          "description": "Job status",
          "title": "Status",
          "type": "string"
        },
        "queue_position": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Position in queue",
          "title": "Queue Position"
        },
        "priority": {
          "description": "Job priority",
          "title": "Priority",
          "type": "integer"
        },
        "created_at": {
          "description": "Job creation time",
          "format": "date-time",
          "title": "Created At",
          "type": "string"
        },
        "started_at": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Job start time",
          "title": "Started At"
        },
        "completed_at": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Job completion time",
          "title": "Completed At"
        },
        "current_stage": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Current processing stage",
          "title": "Current Stage"
        },
        "progress_percentage": {
          "description": "Overall progress percentage",
          "title": "Progress Percentage",
          "type": "number"
        },
        "estimated_completion": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Estimated completion time",
          "title": "Estimated Completion"
        },
        "result_metadata": {
          "anyOf": [
            {
              "additionalProperties": true,
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Processing results",
          "title": "Result Metadata"
        },
        "error_message": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Error message if failed",
          "title": "Error Message"
        },
        "error_code": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Error code if failed",
          "title": "Error Code"
        },
        "retry_count": {
          "description": "Number of retry attempts",
          "title": "Retry Count",
          "type": "integer"
        },
        "processing_duration": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Processing time in seconds",
          "title": "Processing Duration"
        },
        "cpu_time": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "CPU time used",
          "title": "Cpu Time"
        },
        "memory_peak": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Peak memory usage in bytes",
          "title": "Memory Peak"
        }
      },
      "required": [
        "id",
        "input_file_id",
        "processing_mode",
        "settings",
        "status",
        "priority",
        "created_at",
        "progress_percentage",
        "retry_count"
      ],
      "title": "ProcessingJobResponse",
      "type": "object"
    }
  },
  "description": "Detailed processing job response with progress history.",
  "properties": {
    "job": {
      "$ref": "#/$defs/ProcessingJobResponse",
      "description": "Job information"
    },
    "progress_history": {
      "description": "Progress history",
      "items": {
        "$ref": "#/$defs/JobProgressResponse"
      },
      "title": "Progress History",
      "type": "array"
    },
    "input_file": {
      "anyOf": [
        {
          "additionalProperties": true,
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Input file information",
      "title": "Input File"
    },
    "reference_file": {
      "anyOf": [
        {
          "additionalProperties": true,
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Reference file information",
      "title": "Reference File"
    },
    "output_file": {
      "anyOf": [
        {
          "additionalProperties": true,
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Output file information",
      "title": "Output File"
    }
  },
  "required": [
    "job",
    "progress_history"
  ],
  "title": "ProcessingJobDetailResponse",
  "type": "object"
}
```

---

### JobProgressResponse

**Description:** Job progress response model.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `id` | `<class 'uuid.UUID'>` | ✅ | `PydanticUndefined` | Progress entry ID |  |
| `job_id` | `<class 'uuid.UUID'>` | ✅ | `PydanticUndefined` | Associated job ID |  |
| `stage` | `<class 'str'>` | ✅ | `PydanticUndefined` | Processing stage |  |
| `progress_percentage` | `<class 'float'>` | ✅ | `PydanticUndefined` | Stage progress percentage |  |
| `message` | `typing.Optional[str]` | ❌ | `None` | Progress message |  |
| `timestamp` | `<class 'datetime.datetime'>` | ✅ | `PydanticUndefined` | Progress timestamp |  |
| `stage_started_at` | `typing.Optional[datetime.datetime]` | ❌ | `None` | Stage start time |  |
| `stage_duration` | `typing.Optional[float]` | ❌ | `None` | Stage duration in seconds |  |
| `details` | `typing.Optional[typing.Dict[str, typing.Any]]` | ❌ | `None` | Additional details |  |
| `warnings` | `typing.Optional[typing.Dict[str, typing.Any]]` | ❌ | `None` | Stage warnings |  |

**JSON Schema:**
```json
{
  "description": "Job progress response model.",
  "properties": {
    "id": {
      "description": "Progress entry ID",
      "format": "uuid",
      "title": "Id",
      "type": "string"
    },
    "job_id": {
      "description": "Associated job ID",
      "format": "uuid",
      "title": "Job Id",
      "type": "string"
    },
    "stage": {
      "description": "Processing stage",
      "title": "Stage",
      "type": "string"
    },
    "progress_percentage": {
      "description": "Stage progress percentage",
      "title": "Progress Percentage",
      "type": "number"
    },
    "message": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Progress message",
      "title": "Message"
    },
    "timestamp": {
      "description": "Progress timestamp",
      "format": "date-time",
      "title": "Timestamp",
      "type": "string"
    },
    "stage_started_at": {
      "anyOf": [
        {
          "format": "date-time",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Stage start time",
      "title": "Stage Started At"
    },
    "stage_duration": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Stage duration in seconds",
      "title": "Stage Duration"
    },
    "details": {
      "anyOf": [
        {
          "additionalProperties": true,
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Additional details",
      "title": "Details"
    },
    "warnings": {
      "anyOf": [
        {
          "additionalProperties": true,
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Stage warnings",
      "title": "Warnings"
    }
  },
  "required": [
    "id",
    "job_id",
    "stage",
    "progress_percentage",
    "timestamp"
  ],
  "title": "JobProgressResponse",
  "type": "object"
}
```

---

### ProcessingStatsResponse

**Description:** Processing statistics response.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `total_jobs` | `<class 'int'>` | ✅ | `PydanticUndefined` | Total number of jobs |  |
| `jobs_by_status` | `typing.Dict[str, int]` | ✅ | `PydanticUndefined` | Job count by status |  |
| `jobs_by_mode` | `typing.Dict[str, int]` | ✅ | `PydanticUndefined` | Job count by processing mode |  |
| `average_processing_time` | `<class 'float'>` | ✅ | `PydanticUndefined` | Average processing time in seconds |  |
| `queue_length` | `<class 'int'>` | ✅ | `PydanticUndefined` | Current queue length |  |
| `active_workers` | `<class 'int'>` | ✅ | `PydanticUndefined` | Number of active workers |  |
| `jobs_completed_24h` | `<class 'int'>` | ✅ | `PydanticUndefined` | Jobs completed in last 24 hours |  |
| `jobs_failed_24h` | `<class 'int'>` | ✅ | `PydanticUndefined` | Jobs failed in last 24 hours |  |
| `average_wait_time` | `<class 'float'>` | ✅ | `PydanticUndefined` | Average queue wait time in seconds |  |

**JSON Schema:**
```json
{
  "description": "Processing statistics response.",
  "properties": {
    "total_jobs": {
      "description": "Total number of jobs",
      "title": "Total Jobs",
      "type": "integer"
    },
    "jobs_by_status": {
      "additionalProperties": {
        "type": "integer"
      },
      "description": "Job count by status",
      "title": "Jobs By Status",
      "type": "object"
    },
    "jobs_by_mode": {
      "additionalProperties": {
        "type": "integer"
      },
      "description": "Job count by processing mode",
      "title": "Jobs By Mode",
      "type": "object"
    },
    "average_processing_time": {
      "description": "Average processing time in seconds",
      "title": "Average Processing Time",
      "type": "number"
    },
    "queue_length": {
      "description": "Current queue length",
      "title": "Queue Length",
      "type": "integer"
    },
    "active_workers": {
      "description": "Number of active workers",
      "title": "Active Workers",
      "type": "integer"
    },
    "jobs_completed_24h": {
      "description": "Jobs completed in last 24 hours",
      "title": "Jobs Completed 24H",
      "type": "integer"
    },
    "jobs_failed_24h": {
      "description": "Jobs failed in last 24 hours",
      "title": "Jobs Failed 24H",
      "type": "integer"
    },
    "average_wait_time": {
      "description": "Average queue wait time in seconds",
      "title": "Average Wait Time",
      "type": "number"
    }
  },
  "required": [
    "total_jobs",
    "jobs_by_status",
    "jobs_by_mode",
    "average_processing_time",
    "queue_length",
    "active_workers",
    "jobs_completed_24h",
    "jobs_failed_24h",
    "average_wait_time"
  ],
  "title": "ProcessingStatsResponse",
  "type": "object"
}
```

---

### ProcessingModeInfo

**Description:** Processing mode information.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `mode` | `<class 'str'>` | ✅ | `PydanticUndefined` | Processing mode name |  |
| `display_name` | `<class 'str'>` | ✅ | `PydanticUndefined` | Human-readable mode name |  |
| `description` | `<class 'str'>` | ✅ | `PydanticUndefined` | Mode description |  |
| `requires_reference` | `<class 'bool'>` | ✅ | `PydanticUndefined` | Whether mode requires reference file |  |
| `estimated_duration` | `<class 'float'>` | ✅ | `PydanticUndefined` | Estimated processing duration in seconds |  |
| `settings_schema` | `typing.Dict[str, typing.Any]` | ✅ | `PydanticUndefined` | JSON schema for settings |  |

**JSON Schema:**
```json
{
  "description": "Processing mode information.",
  "properties": {
    "mode": {
      "description": "Processing mode name",
      "title": "Mode",
      "type": "string"
    },
    "display_name": {
      "description": "Human-readable mode name",
      "title": "Display Name",
      "type": "string"
    },
    "description": {
      "description": "Mode description",
      "title": "Description",
      "type": "string"
    },
    "requires_reference": {
      "description": "Whether mode requires reference file",
      "title": "Requires Reference",
      "type": "boolean"
    },
    "estimated_duration": {
      "description": "Estimated processing duration in seconds",
      "title": "Estimated Duration",
      "type": "number"
    },
    "settings_schema": {
      "additionalProperties": true,
      "description": "JSON schema for settings",
      "title": "Settings Schema",
      "type": "object"
    }
  },
  "required": [
    "mode",
    "display_name",
    "description",
    "requires_reference",
    "estimated_duration",
    "settings_schema"
  ],
  "title": "ProcessingModeInfo",
  "type": "object"
}
```

---

### ProcessingModesResponse

**Description:** Available processing modes response.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `modes` | `typing.List[app.schemas.processing.ProcessingModeInfo]` | ✅ | `PydanticUndefined` | Available processing modes |  |
| `default_mode` | `<class 'str'>` | ✅ | `PydanticUndefined` | Default processing mode |  |

**JSON Schema:**
```json
{
  "$defs": {
    "ProcessingModeInfo": {
      "description": "Processing mode information.",
      "properties": {
        "mode": {
          "description": "Processing mode name",
          "title": "Mode",
          "type": "string"
        },
        "display_name": {
          "description": "Human-readable mode name",
          "title": "Display Name",
          "type": "string"
        },
        "description": {
          "description": "Mode description",
          "title": "Description",
          "type": "string"
        },
        "requires_reference": {
          "description": "Whether mode requires reference file",
          "title": "Requires Reference",
          "type": "boolean"
        },
        "estimated_duration": {
          "description": "Estimated processing duration in seconds",
          "title": "Estimated Duration",
          "type": "number"
        },
        "settings_schema": {
          "additionalProperties": true,
          "description": "JSON schema for settings",
          "title": "Settings Schema",
          "type": "object"
        }
      },
      "required": [
        "mode",
        "display_name",
        "description",
        "requires_reference",
        "estimated_duration",
        "settings_schema"
      ],
      "title": "ProcessingModeInfo",
      "type": "object"
    }
  },
  "description": "Available processing modes response.",
  "properties": {
    "modes": {
      "description": "Available processing modes",
      "items": {
        "$ref": "#/$defs/ProcessingModeInfo"
      },
      "title": "Modes",
      "type": "array"
    },
    "default_mode": {
      "description": "Default processing mode",
      "title": "Default Mode",
      "type": "string"
    }
  },
  "required": [
    "modes",
    "default_mode"
  ],
  "title": "ProcessingModesResponse",
  "type": "object"
}
```

---

### QueueStatusResponse

**Description:** Processing queue status response.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `total_queued` | `<class 'int'>` | ✅ | `PydanticUndefined` | Total jobs in queue |  |
| `by_queue` | `typing.Dict[str, int]` | ✅ | `PydanticUndefined` | Jobs by queue name |  |
| `by_priority` | `typing.Dict[str, int]` | ✅ | `PydanticUndefined` | Jobs by priority level |  |
| `estimated_wait_time` | `<class 'float'>` | ✅ | `PydanticUndefined` | Estimated wait time in seconds |  |
| `active_workers` | `<class 'int'>` | ✅ | `PydanticUndefined` | Number of active workers |  |
| `worker_capacity` | `<class 'int'>` | ✅ | `PydanticUndefined` | Total worker capacity |  |

**JSON Schema:**
```json
{
  "description": "Processing queue status response.",
  "properties": {
    "total_queued": {
      "description": "Total jobs in queue",
      "title": "Total Queued",
      "type": "integer"
    },
    "by_queue": {
      "additionalProperties": {
        "type": "integer"
      },
      "description": "Jobs by queue name",
      "title": "By Queue",
      "type": "object"
    },
    "by_priority": {
      "additionalProperties": {
        "type": "integer"
      },
      "description": "Jobs by priority level",
      "title": "By Priority",
      "type": "object"
    },
    "estimated_wait_time": {
      "description": "Estimated wait time in seconds",
      "title": "Estimated Wait Time",
      "type": "number"
    },
    "active_workers": {
      "description": "Number of active workers",
      "title": "Active Workers",
      "type": "integer"
    },
    "worker_capacity": {
      "description": "Total worker capacity",
      "title": "Worker Capacity",
      "type": "integer"
    }
  },
  "required": [
    "total_queued",
    "by_queue",
    "by_priority",
    "estimated_wait_time",
    "active_workers",
    "worker_capacity"
  ],
  "title": "QueueStatusResponse",
  "type": "object"
}
```

---

### CeleryWorkerStatusSchema

**Description:** Celery worker status information.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `worker_id` | `<class 'str'>` | ✅ | `PydanticUndefined` | Unique worker identifier |  |
| `hostname` | `<class 'str'>` | ✅ | `PydanticUndefined` | Worker hostname |  |
| `status` | `typing.Literal['online', 'offline', 'unknown']` | ✅ | `PydanticUndefined` | Worker status |  |
| `active_tasks` | `<class 'int'>` | ✅ | `PydanticUndefined` | Number of currently active tasks |  |
| `processed_tasks` | `<class 'int'>` | ✅ | `PydanticUndefined` | Total number of processed tasks |  |
| `load_average` | `typing.List[float]` | ❌ | `[]` | System load average [1min, 5min, 15min] |  |
| `memory_usage` | `typing.Dict[str, typing.Any]` | ❌ | `{}` | Memory usage statistics |  |
| `queues` | `typing.List[str]` | ❌ | `[]` | Queues this worker is listening to |  |
| `last_heartbeat` | `typing.Optional[datetime.datetime]` | ❌ | `None` | Last heartbeat timestamp |  |

**JSON Schema:**
```json
{
  "description": "Celery worker status information.",
  "properties": {
    "worker_id": {
      "description": "Unique worker identifier",
      "title": "Worker Id",
      "type": "string"
    },
    "hostname": {
      "description": "Worker hostname",
      "title": "Hostname",
      "type": "string"
    },
    "status": {
      "description": "Worker status",
      "enum": [
        "online",
        "offline",
        "unknown"
      ],
      "title": "Status",
      "type": "string"
    },
    "active_tasks": {
      "description": "Number of currently active tasks",
      "minimum": 0,
      "title": "Active Tasks",
      "type": "integer"
    },
    "processed_tasks": {
      "description": "Total number of processed tasks",
      "minimum": 0,
      "title": "Processed Tasks",
      "type": "integer"
    },
    "load_average": {
      "default": [],
      "description": "System load average [1min, 5min, 15min]",
      "items": {
        "type": "number"
      },
      "title": "Load Average",
      "type": "array"
    },
    "memory_usage": {
      "additionalProperties": true,
      "default": {},
      "description": "Memory usage statistics",
      "title": "Memory Usage",
      "type": "object"
    },
    "queues": {
      "default": [],
      "description": "Queues this worker is listening to",
      "items": {
        "type": "string"
      },
      "title": "Queues",
      "type": "array"
    },
    "last_heartbeat": {
      "anyOf": [
        {
          "format": "date-time",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Last heartbeat timestamp",
      "title": "Last Heartbeat"
    }
  },
  "required": [
    "worker_id",
    "hostname",
    "status",
    "active_tasks",
    "processed_tasks"
  ],
  "title": "CeleryWorkerStatusSchema",
  "type": "object"
}
```

---

### CeleryStatusSchema

**Description:** Overall Celery system status.

**Fields:**

| Field | Type | Required | Default | Description | Constraints |
|-------|------|----------|---------|-------------|-------------|
| `total_workers` | `<class 'int'>` | ✅ | `PydanticUndefined` | Total number of workers |  |
| `active_workers` | `<class 'int'>` | ✅ | `PydanticUndefined` | Number of active workers |  |
| `offline_workers` | `<class 'int'>` | ✅ | `PydanticUndefined` | Number of offline workers |  |
| `pending_tasks` | `<class 'int'>` | ✅ | `PydanticUndefined` | Number of pending tasks in all queues |  |
| `active_tasks` | `<class 'int'>` | ✅ | `PydanticUndefined` | Number of currently executing tasks |  |
| `failed_tasks_recent` | `<class 'int'>` | ✅ | `PydanticUndefined` | Number of failed tasks in last hour |  |
| `queue_lengths` | `typing.Dict[str, int]` | ❌ | `{}` | Length of each queue |  |
| `workers` | `typing.List[app.schemas.settings.CeleryWorkerStatusSchema]` | ❌ | `[]` | Individual worker statuses |  |
| `broker_status` | `typing.Literal['connected', 'disconnected', 'unknown']` | ✅ | `PydanticUndefined` | Redis broker connection status |  |
| `last_updated` | `<class 'datetime.datetime'>` | ✅ | `PydanticUndefined` | When this status was last updated |  |

**JSON Schema:**
```json
{
  "$defs": {
    "CeleryWorkerStatusSchema": {
      "description": "Celery worker status information.",
      "properties": {
        "worker_id": {
          "description": "Unique worker identifier",
          "title": "Worker Id",
          "type": "string"
        },
        "hostname": {
          "description": "Worker hostname",
          "title": "Hostname",
          "type": "string"
        },
        "status": {
          "description": "Worker status",
          "enum": [
            "online",
            "offline",
            "unknown"
          ],
          "title": "Status",
          "type": "string"
        },
        "active_tasks": {
          "description": "Number of currently active tasks",
          "minimum": 0,
          "title": "Active Tasks",
          "type": "integer"
        },
        "processed_tasks": {
          "description": "Total number of processed tasks",
          "minimum": 0,
          "title": "Processed Tasks",
          "type": "integer"
        },
        "load_average": {
          "default": [],
          "description": "System load average [1min, 5min, 15min]",
          "items": {
            "type": "number"
          },
          "title": "Load Average",
          "type": "array"
        },
        "memory_usage": {
          "additionalProperties": true,
          "default": {},
          "description": "Memory usage statistics",
          "title": "Memory Usage",
          "type": "object"
        },
        "queues": {
          "default": [],
          "description": "Queues this worker is listening to",
          "items": {
            "type": "string"
          },
          "title": "Queues",
          "type": "array"
        },
        "last_heartbeat": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Last heartbeat timestamp",
          "title": "Last Heartbeat"
        }
      },
      "required": [
        "worker_id",
        "hostname",
        "status",
        "active_tasks",
        "processed_tasks"
      ],
      "title": "CeleryWorkerStatusSchema",
      "type": "object"
    }
  },
  "description": "Overall Celery system status.",
  "properties": {
    "total_workers": {
      "description": "Total number of workers",
      "minimum": 0,
      "title": "Total Workers",
      "type": "integer"
    },
    "active_workers": {
      "description": "Number of active workers",
      "minimum": 0,
      "title": "Active Workers",
      "type": "integer"
    },
    "offline_workers": {
      "description": "Number of offline workers",
      "minimum": 0,
      "title": "Offline Workers",
      "type": "integer"
    },
    "pending_tasks": {
      "description": "Number of pending tasks in all queues",
      "minimum": 0,
      "title": "Pending Tasks",
      "type": "integer"
    },
    "active_tasks": {
      "description": "Number of currently executing tasks",
      "minimum": 0,
      "title": "Active Tasks",
      "type": "integer"
    },
    "failed_tasks_recent": {
      "description": "Number of failed tasks in last hour",
      "minimum": 0,
      "title": "Failed Tasks Recent",
      "type": "integer"
    },
    "queue_lengths": {
      "additionalProperties": {
        "type": "integer"
      },
      "default": {},
      "description": "Length of each queue",
      "title": "Queue Lengths",
      "type": "object"
    },
    "workers": {
      "default": [],
      "description": "Individual worker statuses",
      "items": {
        "$ref": "#/$defs/CeleryWorkerStatusSchema"
      },
      "title": "Workers",
      "type": "array"
    },
    "broker_status": {
      "description": "Redis broker connection status",
      "enum": [
        "connected",
        "disconnected",
        "unknown"
      ],
      "title": "Broker Status",
      "type": "string"
    },
    "last_updated": {
      "description": "When this status was last updated",
      "format": "date-time",
      "title": "Last Updated",
      "type": "string"
    }
  },
  "required": [
    "total_workers",
    "active_workers",
    "offline_workers",
    "pending_tasks",
    "active_tasks",
    "failed_tasks_recent",
    "broker_status",
    "last_updated"
  ],
  "title": "CeleryStatusSchema",
  "type": "object"
}
```

---

## Enumerations

### ModelSelectionStrategy

**Description:** Model selection strategy options.

**Valid Values:**
- `auto`
- `performance`
- `quality`
- `custom`

---

### QualityPreference

**Description:** Quality vs speed preference options.

**Valid Values:**
- `fast`
- `balanced`
- `quality`

---

### FallbackStrategy

**Description:** Fallback strategy when primary models fail.

**Valid Values:**
- `strict`
- `graceful`
- `aggressive`

---

### ModelType

**Description:** Types of AI models available.

**Valid Values:**
- `huggingface`
- `ast`
- `custom`

---

## Validation Rules

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
