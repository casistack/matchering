"""
Enterprise Ensemble Configuration

Configuration settings for the ensemble genre classification system.
Allows for safe A/B testing and gradual rollout of new AI models.
"""

import os
from typing import Dict, Any


class EnsembleSettings:
    """Enterprise configuration settings for ensemble AI system."""
    
    # Main feature flags
    ENABLE_ENSEMBLE_AI = os.getenv("ENABLE_ENSEMBLE_AI", "true").lower() == "true"
    ENABLE_HUGGINGFACE_MODELS = os.getenv("ENABLE_HUGGINGFACE_MODELS", "true").lower() == "true"
    ENABLE_A_B_TESTING = os.getenv("ENABLE_A_B_TESTING", "true").lower() == "true"
    
    # Model weights for ensemble voting
    HUGGINGFACE_MODELS_WEIGHT = float(os.getenv("HUGGINGFACE_MODELS_WEIGHT", "0.70"))
    AST_MODEL_WEIGHT = float(os.getenv("AST_MODEL_WEIGHT", "0.25"))
    FALLBACK_WEIGHT = float(os.getenv("FALLBACK_WEIGHT", "0.05"))
    
    # Confidence thresholds
    MIN_CONFIDENCE_THRESHOLD = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.6"))
    ENSEMBLE_AGREEMENT_THRESHOLD = float(os.getenv("ENSEMBLE_AGREEMENT_THRESHOLD", "0.8"))
    
    # Performance and monitoring
    ENABLE_PERFORMANCE_LOGGING = os.getenv("ENABLE_PERFORMANCE_LOGGING", "true").lower() == "true"
    ENABLE_AUDIT_LOGGING = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
    TRACK_MODEL_ACCURACY = os.getenv("TRACK_MODEL_ACCURACY", "true").lower() == "true"
    
    # Safety features
    ENABLE_GRACEFUL_DEGRADATION = os.getenv("ENABLE_GRACEFUL_DEGRADATION", "true").lower() == "true"
    MAX_PROCESSING_TIME_MS = int(os.getenv("MAX_PROCESSING_TIME_MS", "5000"))
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return {
            "feature_flags": {
                "ensemble_ai_enabled": cls.ENABLE_ENSEMBLE_AI,
                "huggingface_models_enabled": cls.ENABLE_HUGGINGFACE_MODELS,
                "a_b_testing_enabled": cls.ENABLE_A_B_TESTING,
            },
            "model_weights": {
                "huggingface_models": cls.HUGGINGFACE_MODELS_WEIGHT,
                "ast_model": cls.AST_MODEL_WEIGHT,
                "fallback": cls.FALLBACK_WEIGHT,
            },
            "thresholds": {
                "min_confidence": cls.MIN_CONFIDENCE_THRESHOLD,
                "ensemble_agreement": cls.ENSEMBLE_AGREEMENT_THRESHOLD,
            },
            "monitoring": {
                "performance_logging": cls.ENABLE_PERFORMANCE_LOGGING,
                "audit_logging": cls.ENABLE_AUDIT_LOGGING,
                "accuracy_tracking": cls.TRACK_MODEL_ACCURACY,
            },
            "safety": {
                "graceful_degradation": cls.ENABLE_GRACEFUL_DEGRADATION,
                "max_processing_time_ms": cls.MAX_PROCESSING_TIME_MS,
            }
        }
    
    @classmethod
    def is_ensemble_enabled(cls) -> bool:
        """Check if ensemble AI should be used."""
        return cls.ENABLE_ENSEMBLE_AI and cls.ENABLE_CNN_ENSEMBLE
    
    @classmethod
    def should_fallback_to_ast(cls) -> bool:
        """Check if we should fallback to AST model only."""
        return not cls.ENABLE_ENSEMBLE_AI or not cls.ENABLE_CNN_ENSEMBLE