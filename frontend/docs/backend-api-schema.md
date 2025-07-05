# Backend API Schema Documentation

**Generated:** 2025-07-05T11:27:42.362983  
**Version:** 1.0.0

This document provides comprehensive reference documentation for the Matchering backend API schemas. All schemas are auto-generated from the actual Pydantic models to ensure accuracy.

## Table of Contents

1. [API Endpoints](#api-endpoints)
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
| `last_updated` | `<class 'datetime.datetime'>` | ✅ | `PydanticUndefined` |  |  |

**JSON Schema:**
```json
{
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
    "last_updated"
  ],
  "title": "SystemStatusResponse",
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

#### Ensemble Weights
- **Must sum to approximately 1.0** (between 0.9 and 1.1)
- **Example:** `{"huggingface_ensemble": 0.7, "ast_model": 0.25, "fallback_classifier": 0.05}`
- **Total:** 0.7 + 0.25 + 0.05 = 1.0 ✅

#### Confidence Threshold  
- **Range:** 0.5 ≤ value ≤ 0.95
- **Example:** `0.6` ✅, `0.4` ❌, `0.98` ❌

#### Max Processing Time
- **Range:** 1000 ≤ value ≤ 10000 (milliseconds)
- **Example:** `5000` ✅, `500` ❌, `15000` ❌

#### Model IDs (Current)
- **HuggingFace Ensemble:** `huggingface_ensemble`
- **Audio Spectrogram Transformer:** `ast_model`  
- **Fallback Classifier:** `fallback_classifier`

## Common Examples

### Update Model Preferences

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

### Create New Profile

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

### Error Response Format

```json
{
  "detail": "Ensemble weights must sum to approximately 1.0, got 0.8",
  "statusCode": 422,
  "field": "ensemble_weights"
}
```

## Notes for Frontend Engineers

1. **Always validate data locally** before sending to backend
2. **Use the exact enum values** listed in this document  
3. **Ensure ensemble weights sum to ~1.0** before submission
4. **Check value ranges** for numeric fields
5. **Handle 422 validation errors** gracefully
6. **Use anonymous_id** for unauthenticated users
7. **All timestamps** are in ISO format (UTC)

---

*This documentation is auto-generated from the actual backend schemas. Last updated: {json_schema['generated_at']}*
