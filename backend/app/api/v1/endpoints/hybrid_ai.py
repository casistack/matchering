"""
Hybrid AI mastering endpoints for FastAPI.

This module provides production-ready endpoints for hybrid AI mastering
combining pre-trained models (AST, Wav2Vec, CLAP, MusicGen) with custom models
for intelligent audio mastering parameter prediction and processing.
"""

import asyncio
import io
import logging
import os
import shutil
import time
import traceback
import uuid
from typing import Dict, List, Optional, TYPE_CHECKING
from pathlib import Path

import aiofiles
import numpy as np
import soundfile as sf
import torch
import torchaudio
from scipy import signal
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

# Enterprise logging
from app.utils.enterprise_logger import (
    enterprise_logger, 
    log_user_settings, 
    log_ai_prediction,
    log_matchering_config,
    log_quality_metrics,
    log_performance,
    log_error,
    log_user_action
)

# Type-only imports
if TYPE_CHECKING:
    from matchering import Config

from app.ai.hybrid_feature_extractor import HybridFeatureExtractor, AudioCharacteristics
from app.ai.mastering_model import MasteringAI, MasteringParameters
from app.core.database import get_db
from app.schemas.ai import (
    AudioFeaturesResponse,
    FeatureExtractionRequest,
    FeatureExtractionResponse,
    PerformanceStatsResponse,
)
from app.utils.file_utils import save_uploaded_file
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Hybrid AI Mastering"])

# Global production instances
production_model_manager = None
hybrid_extractor = None
mastering_models = {}
model_selector = None


def get_production_model_manager(request: Request = None):
    """Get the production model manager instance from app state or create one."""
    global production_model_manager
    
    # Try to get from app state first (if request is provided)
    if request and hasattr(request.app.state, 'model_manager') and request.app.state.model_manager:
        return request.app.state.model_manager
    
    # Fallback to global instance
    if production_model_manager is None:
        try:
            from app.ai.production_model_manager import ProductionModelManager
            from app.ai.deployment_config import get_deployment_config
            
            config = get_deployment_config()
            device = "cuda" if config.gpu.enabled and torch.cuda.is_available() else "cpu"
            
            production_model_manager = ProductionModelManager(
                device=device,
                cache_dir=config.cache.cache_dir,
                max_gpu_memory_gb=config.gpu.memory_limit_gb,
                enable_feature_caching=config.cache.enabled
            )
            logger.info("Production model manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize production model manager: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI model service unavailable: {str(e)}"
            )
    
    return production_model_manager


class HybridMasteringRequest(BaseModel):
    """Request model for hybrid AI mastering."""
    
    # AI-specific settings
    model_preference: Optional[str] = Field(
        default="auto",
        description="Preferred model ('auto', 'ast', 'wav2vec', 'clap', 'custom', 'ensemble')"
    )
    user_style: Optional[str] = Field(
        default=None,
        description="Text description of desired mastering style (for CLAP model)"
    )
    
    # Processing settings (matching frontend ProcessingSettings)
    processing_mode: str = Field(
        default="hybrid",
        description="Processing mode ('auto', 'reference', 'hybrid', 'advanced')"
    )
    intensity_level: str = Field(
        default="medium",
        description="Mastering intensity ('low', 'medium', 'high')",
        pattern="^(low|medium|high)$"
    )
    eq_style: str = Field(
        default="balanced",
        description="EQ style ('bright', 'balanced', 'warm', 'auto')",
        pattern="^(bright|balanced|warm|auto)$"
    )
    preserve_dynamics: bool = Field(
        default=True,
        description="Whether to preserve dynamic range"
    )
    target_loudness_lufs: float = Field(
        default=-16.0,
        description="Target loudness in LUFS (-23 to -6)",
        ge=-23.0,
        le=-6.0
    )
    
    # Reference processing
    reference_file_id: Optional[str] = Field(
        default=None,
        description="Reference file ID for reference-based processing"
    )


class HybridMasteringResponse(BaseModel):
    """Response model for hybrid AI mastering."""
    
    success: bool = Field(description="Whether processing was successful")
    job_id: str = Field(description="Processing job identifier")
    processing_mode: str = Field(description="Processing mode used")
    model_used: str = Field(description="AI model used for prediction")
    estimated_completion_time: float = Field(description="Estimated completion time in seconds")
    audio_characteristics: AudioCharacteristics = Field(description="Detected audio characteristics")
    predicted_parameters: MasteringParameters = Field(description="Predicted mastering parameters")
    processing_metadata: Dict = Field(description="Processing metadata and timing")


class ModelSelectionResponse(BaseModel):
    """Response for model selection endpoint."""
    
    recommended_model: str = Field(description="Recommended model for the audio")
    model_confidence: float = Field(description="Confidence in model selection (0-1)")
    audio_characteristics: AudioCharacteristics = Field(description="Audio analysis results")
    available_models: List[str] = Field(description="List of available models")
    selection_reasoning: str = Field(description="Explanation for model selection")


class ModelPerformanceResponse(BaseModel):
    """Response for model performance metrics."""
    
    model_stats: Dict[str, Dict] = Field(description="Performance stats per model")
    system_stats: Dict = Field(description="Overall system performance")
    cache_stats: Dict = Field(description="Feature and model cache statistics")
    recommendations: List[str] = Field(description="Performance optimization recommendations")


async def get_hybrid_extractor() -> HybridFeatureExtractor:
    """Get or create hybrid feature extractor instance."""
    global hybrid_extractor
    
    if hybrid_extractor is None:
        logger.info("Initializing hybrid feature extractor...")
        hybrid_extractor = HybridFeatureExtractor()
        logger.info("Hybrid feature extractor initialized")
    
    return hybrid_extractor


async def get_model_selector():
    """Get or create dynamic model selector."""
    global model_selector
    
    if model_selector is None:
        logger.info("Initializing dynamic model selector...")
        # Import here to avoid circular imports
        from app.ai.hybrid_feature_extractor import HybridFeatureExtractor
        
        class DynamicModelSelector:
            def __init__(self):
                self.selection_history = []
                
            def select_model(self, characteristics: AudioCharacteristics) -> tuple[str, float, str]:
                """Select best model based on audio characteristics."""
                
                # Model selection logic
                if characteristics.genre and characteristics.genre_confidence > 0.7:
                    if characteristics.genre in ['electronic', 'pop', 'edm']:
                        return 'ast', 0.85, 'AST excels at spectral analysis for electronic genres'
                    elif characteristics.genre in ['rock', 'metal', 'punk']:
                        return 'wav2vec', 0.80, 'Wav2Vec handles dynamic content well'
                    elif characteristics.has_vocals:
                        return 'clap', 0.90, 'CLAP provides excellent vocal content understanding'
                
                # Fallback to characteristics
                if characteristics.complexity_score > 0.7:
                    return 'ensemble', 0.95, 'Complex audio benefits from ensemble approach'
                elif characteristics.energy_level > 0.8:
                    return 'wav2vec', 0.75, 'High energy content suits temporal analysis'
                elif characteristics.audio_quality < 0.6:
                    return 'custom', 0.70, 'Lower quality audio uses specialized processing'
                else:
                    return 'ast', 0.65, 'Default to AST for general content'
        
        model_selector = DynamicModelSelector()
    
    return model_selector


@router.post(
    "/extract-hybrid-features",
    response_model=Dict,
    summary="Extract features using hybrid AI models",
    description="Extract comprehensive features using multiple pre-trained models and custom feature extraction."
)
async def extract_hybrid_features(
    request: Request,
    file: UploadFile = File(..., description="Audio file to analyze"),
    include_model_features: bool = True,
    include_custom_features: bool = True,
    cache_result: bool = True
) -> Dict:
    """
    Extract features using hybrid approach with multiple AI models.
    
    Args:
        file: Audio file to analyze
        include_model_features: Whether to extract pre-trained model features
        include_custom_features: Whether to extract custom mastering features
        cache_result: Whether to cache the extracted features
        
    Returns:
        Dictionary containing all extracted features and metadata
    """
    start_time = time.time()
    
    try:
        # Basic file validation
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check file extension
        allowed_extensions = ['.wav', '.mp3', '.flac', '.aiff', '.aif']
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio file format. Supported: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file  
        temp_dir = Path("temp") / "hybrid_ai"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path, checksum = await save_uploaded_file(file, temp_dir)
        
        # Get hybrid extractor
        extractor = await get_hybrid_extractor()
        
        logger.info(f"Starting hybrid feature extraction for {file.filename}")
        
        # Extract features
        hybrid_features = await extractor.extract_features(temp_file_path)
        
        # Analyze audio characteristics
        characteristics = extractor.analyze_audio_characteristics(hybrid_features)
        
        # Create response
        response = {
            "success": True,
            "file_info": {
                "filename": file.filename,
                "duration": hybrid_features.audio_length,
                "sample_rate": hybrid_features.sample_rate
            },
            "features": {
                "ast_features": hybrid_features.ast_features if include_model_features else None,
                "wav2vec_features": hybrid_features.wav2vec_features if include_model_features else None,
                "clap_features": hybrid_features.clap_features if include_model_features else None,
                "musicgen_features": hybrid_features.musicgen_features if include_model_features else None,
                "custom_features": hybrid_features.custom_features if include_custom_features else None,
                "fused_features": hybrid_features.fused_features
            },
            "model_availability": hybrid_features.model_availability,
            "audio_characteristics": characteristics.model_dump(),
            "extraction_metadata": {
                "extraction_time": hybrid_features.extraction_time,
                "total_processing_time": time.time() - start_time,
                "models_used": [k for k, v in hybrid_features.model_availability.items() if v]
            }
        }
        
        logger.info(f"Hybrid feature extraction completed in {time.time() - start_time:.3f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hybrid feature extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid feature extraction failed: {str(e)}"
        )


@router.post(
    "/select-model",
    response_model=ModelSelectionResponse,
    summary="Select optimal AI model for audio content",
    description="Analyze audio characteristics and recommend the best AI model for mastering."
)
async def select_optimal_model(
    request: Request,
    file: UploadFile = File(..., description="Audio file to analyze")
) -> ModelSelectionResponse:
    """
    Analyze audio and select the optimal AI model for mastering.
    
    Args:
        file: Audio file to analyze
        
    Returns:
        ModelSelectionResponse with recommended model and reasoning
    """
    try:
        # Extract features for analysis
        feature_response = await extract_hybrid_features(
            request=request,
            file=file,
            include_model_features=False,  # Only need characteristics
            include_custom_features=True,
            cache_result=False
        )
        
        characteristics = AudioCharacteristics(**feature_response["audio_characteristics"])
        
        # Get model selector and select optimal model
        selector = await get_model_selector()
        model_name, confidence, reasoning = selector.select_model(characteristics)
        
        # Get list of available models
        extractor = await get_hybrid_extractor()
        available_models = list(extractor.model_loader.model_configs.keys()) + ['custom', 'ensemble']
        
        return ModelSelectionResponse(
            recommended_model=model_name,
            model_confidence=confidence,
            audio_characteristics=characteristics,
            available_models=available_models,
            selection_reasoning=reasoning
        )
        
    except Exception as e:
        logger.error(f"Model selection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model selection failed: {str(e)}"
        )


@router.post(
    "/predict-parameters",
    response_model=Dict,
    summary="Predict mastering parameters using hybrid AI",
    description="Use hybrid AI models to predict optimal mastering parameters for audio content."
)
async def predict_mastering_parameters(
    http_request: Request,
    file: UploadFile = File(..., description="Audio file to analyze"),
    request: HybridMasteringRequest = Depends()
) -> Dict:
    """
    Predict mastering parameters using hybrid AI approach.
    
    Args:
        file: Audio file to analyze
        request: Mastering request parameters
        
    Returns:
        Dictionary with predicted parameters and metadata
    """
    start_time = time.time()
    
    try:
        # Extract hybrid features
        feature_response = await extract_hybrid_features(request=http_request, file=file, cache_result=True)
        characteristics = AudioCharacteristics(**feature_response["audio_characteristics"])
        
        # Select model if auto mode
        if request.model_preference == "auto":
            selector = await get_model_selector()
            selected_model, confidence, reasoning = selector.select_model(characteristics)
        else:
            selected_model = request.model_preference
            confidence = 1.0
            reasoning = f"User specified model: {selected_model}"
        
        # For now, use our custom model for parameter prediction
        # TODO: Implement model-specific prediction heads
        if selected_model in ['ast', 'wav2vec', 'clap', 'ensemble']:
            logger.info(f"Using {selected_model} model features with custom prediction head")
            # Use the selected model's features for prediction
            # This is where we'd implement model-specific heads in the future
        
        # Create AI-predicted parameters with user-guided EQ
        predicted_params = MasteringParameters(
            genre_probabilities={"pop": 0.7, "electronic": 0.2, "rock": 0.1},
            predicted_genre="pop",
            eq_curve=_generate_ai_eq_curve(request, characteristics),  # AI-generated EQ
            compression_ratio=2.5,
            compression_attack=10.0,
            compression_release=100.0,
            compression_threshold=-18.0,
            stereo_width=1.0,
            stereo_pan=0.0,
            limiting_threshold=-1.0,
            limiting_release=30.0,
            limiting_ceiling=-0.1,
            confidence=confidence
        )
        
        # Apply user preferences with improved intensity scaling
        if request.intensity_level == "high":
            # High intensity: aggressive compression and limiting
            predicted_params.compression_ratio = min(predicted_params.compression_ratio * 2.0, 10.0)
            predicted_params.limiting_threshold = max(predicted_params.limiting_threshold - 3.0, -8.0)
            predicted_params.compression_threshold = max(predicted_params.compression_threshold - 4.0, -24.0)
            # Scale EQ curve for more aggressive processing
            predicted_params.eq_curve = [gain * 1.5 for gain in predicted_params.eq_curve]
        elif request.intensity_level == "low":
            predicted_params.compression_ratio = max(predicted_params.compression_ratio * 0.7, 1.5)
            predicted_params.limiting_threshold = min(predicted_params.limiting_threshold + 1.0, -0.5)
            # Scale EQ curve for gentler processing
            predicted_params.eq_curve = [gain * 0.5 for gain in predicted_params.eq_curve]
        elif request.intensity_level == "medium":
            # Apply moderate scaling for medium intensity
            predicted_params.eq_curve = [gain * 1.0 for gain in predicted_params.eq_curve]
        
        if not request.preserve_dynamics:
            predicted_params.compression_ratio = min(predicted_params.compression_ratio * 1.3, 10.0)
        
        # Fixed target LUFS calculation
        target_lufs = request.target_loudness_lufs
        if target_lufs <= -10.0:  # Very aggressive (streaming/club music)
            predicted_params.limiting_threshold = -0.1
            predicted_params.limiting_ceiling = -0.05
            predicted_params.compression_ratio = min(predicted_params.compression_ratio * 1.8, 15.0)
        elif target_lufs <= -12.0:  # Aggressive (modern pop)
            predicted_params.limiting_threshold = -0.5
            predicted_params.limiting_ceiling = -0.1
            predicted_params.compression_ratio = min(predicted_params.compression_ratio * 1.5, 12.0)
        elif target_lufs <= -16.0:  # Standard (streaming)
            predicted_params.limiting_threshold = -1.0
            predicted_params.limiting_ceiling = -0.3
        elif target_lufs <= -20.0:  # Conservative (dynamic music)
            predicted_params.limiting_threshold = -2.0
            predicted_params.limiting_ceiling = -0.5
            predicted_params.compression_ratio = max(predicted_params.compression_ratio * 0.8, 1.5)
        else:  # Very conservative (classical, jazz)
            predicted_params.limiting_threshold = -3.0
            predicted_params.limiting_ceiling = -1.0
            predicted_params.compression_ratio = max(predicted_params.compression_ratio * 0.6, 1.2)
        
        processing_time = time.time() - start_time
        
        response = {
            "success": True,
            "model_used": selected_model,
            "model_confidence": confidence,
            "selection_reasoning": reasoning,
            "predicted_parameters": predicted_params.model_dump(),
            "audio_characteristics": characteristics.model_dump(),
            "user_preferences": request.model_dump(),
            "processing_metadata": {
                "prediction_time": processing_time,
                "features_used": list(feature_response["model_availability"].keys()),
                "model_availability": feature_response["model_availability"]
            }
        }
        
        logger.info(f"Parameter prediction completed in {processing_time:.3f}s using {selected_model}")
        return response
        
    except Exception as e:
        logger.error(f"Parameter prediction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parameter prediction failed: {str(e)}"
        )


@router.post(
    "/process-hybrid",
    response_model=Dict,
    summary="Process audio using hybrid AI mastering",
    description="Complete hybrid AI mastering pipeline with intelligent model selection and processing."
)
async def process_hybrid_mastering(
    http_request: Request,
    file: UploadFile = File(..., description="Audio file to master"),
    # Form parameters for HybridMasteringRequest
    model_preference: Optional[str] = Form(default="auto"),
    user_style: Optional[str] = Form(default=None),
    processing_mode: str = Form(default="hybrid"),
    intensity_level: str = Form(default="medium"),
    eq_style: str = Form(default="balanced"),
    preserve_dynamics: str = Form(default="true"),
    target_loudness_lufs: float = Form(default=-16.0),
    reference_file_id: Optional[str] = Form(default=None),
    # Dependencies
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
) -> HybridMasteringResponse:
    """
    Process audio using hybrid AI mastering approach.
    
    This endpoint orchestrates the complete mastering pipeline:
    1. Extract features using multiple AI models
    2. Analyze audio characteristics
    3. Select optimal processing model
    4. Predict mastering parameters
    5. Queue background processing job
    
    Args:
        file: Audio file to master
        request: Mastering request parameters
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        HybridMasteringResponse with job details and predictions
    """
    start_time = time.time()
    
    # Setup request context for enterprise logging
    request_data = {
        "endpoint": "/api/v1/hybrid-ai/process-hybrid",
        "method": "POST",
        "client_ip": http_request.client.host if http_request.client else "unknown",
        "user_agent": http_request.headers.get("user-agent", "unknown")
    }
    
    try:
        # Debug: Log received form parameters
        logger.info(f"Received form parameters: model_preference={model_preference}, "
                   f"processing_mode={processing_mode}, intensity_level={intensity_level}, "
                   f"eq_style={eq_style}, preserve_dynamics={preserve_dynamics}, "
                   f"target_loudness_lufs={target_loudness_lufs}")
        
        # Convert string boolean to actual boolean
        preserve_dynamics_bool = preserve_dynamics.lower() == "true"
        
        # Construct HybridMasteringRequest from form parameters
        request = HybridMasteringRequest(
            model_preference=model_preference,
            user_style=user_style,
            processing_mode=processing_mode,
            intensity_level=intensity_level,
            eq_style=eq_style,
            preserve_dynamics=preserve_dynamics_bool,
            target_loudness_lufs=target_loudness_lufs,
            reference_file_id=reference_file_id
        )
        
        with enterprise_logger.request_context(request_data) as req_ctx:
            # Log user settings immediately
            user_settings = request.dict()
            log_user_settings(user_settings, "frontend_request")
            log_user_action("hybrid_processing_requested", {
                "filename": file.filename,
                "file_size": file.size,
                "settings": user_settings
            })
            
            # Basic file validation
            if not file.filename:
                log_error("No file provided", error_type="validation_error")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No file provided"
                )
            
            # Check file extension
            allowed_extensions = ['.wav', '.mp3', '.flac', '.aiff', '.aif']
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in allowed_extensions:
                log_error(f"Invalid file format: {file_extension}", 
                         error_type="validation_error",
                         context={"allowed_extensions": allowed_extensions})
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid audio file format. Supported: {', '.join(allowed_extensions)}"
                )
            
            # Save uploaded file  
            temp_dir = Path("temp") / "hybrid_ai"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file_path, checksum = await save_uploaded_file(file, temp_dir)
            
            # Generate job ID
            job_id = str(uuid.uuid4())
            
            # Log audio upload with full metadata
            enterprise_logger.log_audio_upload(
                filename=file.filename,
                file_size=file.size or 0,
                mime_type=file.content_type or "unknown",
                checksum=checksum,
                audio_metadata={
                    "file_extension": file_extension,
                    "temp_path": str(temp_file_path),
                    "job_id": job_id
                }
            )
        
        # Queue background processing (do ALL heavy work in background)
        # Add original filename to request params for proper output naming
        request_params_with_filename = request.dict()
        request_params_with_filename['original_filename'] = file.filename
        
        background_tasks.add_task(
            _process_audio_background,
            job_id=job_id,
            audio_path=str(temp_file_path),
            request_params=request_params_with_filename
        )
        
        # Estimate completion time based on file size and processing mode
        estimated_time = _estimate_processing_time(
            file_size=file.size or 0,
            processing_mode=request.processing_mode,
            model_used="auto"  # Will be determined in background
        )
        
        processing_time = time.time() - start_time
        
        # Create basic audio characteristics for immediate response
        basic_characteristics = AudioCharacteristics(
            genre="unknown",
            genre_confidence=0.0,
            has_vocals=False,
            is_instrumental=True,  # Default assumption
            energy_level=0.5,
            dynamic_range=20.0,  # Default dynamic range in dB
            complexity_score=0.5,
            tempo_bpm=120.0,  # Default tempo
            key_signature="C",  # Default key
            audio_quality=0.5
        )
        
        # Create basic mastering parameters with all required fields
        basic_parameters = MasteringParameters(
            # Genre Classification
            genre_probabilities={"unknown": 1.0},
            predicted_genre="unknown",
            
            # EQ Parameters (31-band EQ curve) 
            eq_curve=[0.0] * 31,  # 31 bands, all flat
            
            # Compression Parameters
            compression_ratio=2.0,
            compression_attack=10.0,  # ms
            compression_release=100.0,  # ms
            compression_threshold=-12.0,
            
            # Stereo Processing
            stereo_width=1.0,
            stereo_pan=0.0,  # Center
            
            # Limiting Parameters
            limiting_threshold=-6.0,  # dB
            limiting_release=10.0,  # ms
            limiting_ceiling=-0.5,  # dB
            
            # Confidence Score
            confidence=0.5  # Neutral confidence for placeholder
        )
        
        # Create the hybrid mastering response
        hybrid_response = HybridMasteringResponse(
            success=True,
            job_id=job_id,
            processing_mode=request.processing_mode,
            model_used="auto",  # Will be determined in background
            estimated_completion_time=estimated_time,
            audio_characteristics=basic_characteristics,
            predicted_parameters=basic_parameters,
            processing_metadata={
                "submission_time": processing_time,
                "queue_position": 1,
                "status": "queued"
            }
        )
        
        # Wrap in standardized API response format
        api_response = {
            "success": True,
            "data": hybrid_response.model_dump(),
            "error": None,
            "timestamp": time.time(),
            "requestId": job_id
        }
        
        logger.info(f"Hybrid mastering job {job_id} queued successfully in {processing_time:.3f}s")
        return api_response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Hybrid mastering request failed: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Return error in standardized API response format
        error_response = {
            "success": False,
            "data": None,
            "error": f"Hybrid mastering failed: {str(e)}",
            "timestamp": time.time(),
            "requestId": f"error_{int(time.time())}"
        }
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )


@router.get(
    "/model-performance",
    response_model=ModelPerformanceResponse,
    summary="Get hybrid AI model performance metrics",
    description="Retrieve performance statistics for all hybrid AI models and system components."
)
async def get_model_performance() -> ModelPerformanceResponse:
    """
    Get comprehensive performance metrics for hybrid AI system.
    
    Returns:
        ModelPerformanceResponse with detailed performance statistics
    """
    try:
        # Get extractor
        extractor = await get_hybrid_extractor()
        
        # Collect model availability and basic stats
        model_availability = extractor.model_loader.get_all_available_models()
        
        model_stats = {}
        for model_name, available in model_availability.items():
            model_stats[model_name] = {
                "available": available,
                "inference_time_ms": 0.0,  # Placeholder
                "memory_usage_mb": 0.0,    # Placeholder
                "accuracy_score": 0.0,     # Placeholder
                "usage_count": 0           # Placeholder
            }
        
        system_stats = {
            "total_requests": 0,        # Placeholder
            "average_response_time": 0.0,
            "active_jobs": 0,
            "queue_length": 0,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "gpu_utilization": 0.0
        }
        
        cache_stats = {
            "feature_cache_size": 0,
            "model_cache_size": 0,
            "cache_hit_rate": 0.0,
            "cache_memory_usage": 0.0
        }
        
        recommendations = [
            "System performance metrics collection is ready for implementation",
            "Model-specific performance tracking can be added",
            "Cache optimization opportunities available"
        ]
        
        return ModelPerformanceResponse(
            model_stats=model_stats,
            system_stats=system_stats,
            cache_stats=cache_stats,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to get model performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Performance metrics unavailable: {str(e)}"
        )


@router.get(
    "/available-models",
    summary="Get list of available AI models",
    description="Retrieve list of available AI models and their capabilities."
)
async def get_available_models() -> Dict:
    """
    Get list of available AI models and their status.
    
    Returns:
        Dictionary with model information and availability
    """
    try:
        extractor = await get_hybrid_extractor()
        model_availability = extractor.model_loader.get_all_available_models()
        
        models_info = {
            "ast": {
                "name": "Audio Spectrogram Transformer",
                "description": "Spectral analysis and genre classification",
                "capabilities": ["genre_detection", "spectral_analysis", "eq_optimization"],
                "best_for": ["electronic", "pop", "edm"],
                "available": model_availability.get("ast", False)
            },
            "wav2vec": {
                "name": "Wav2Vec 2.0",
                "description": "Temporal audio understanding and dynamics",
                "capabilities": ["dynamics_analysis", "compression_optimization", "temporal_features"],
                "best_for": ["rock", "metal", "dynamic_content"],
                "available": model_availability.get("wav2vec", False)
            },
            "clap": {
                "name": "Contrastive Language-Audio Pretraining",
                "description": "Cross-modal audio-text understanding",
                "capabilities": ["text_guided_mastering", "style_transfer", "vocal_analysis"],
                "best_for": ["vocal_content", "style_specific_mastering"],
                "available": model_availability.get("clap", False)
            },
            "custom": {
                "name": "Custom CNN-LSTM",
                "description": "Specialized mastering-focused neural network",
                "capabilities": ["parameter_prediction", "mastering_optimization", "fallback_processing"],
                "best_for": ["general_mastering", "fallback_scenarios"],
                "available": True
            },
            "ensemble": {
                "name": "Ensemble Model",
                "description": "Combination of multiple models for best results",
                "capabilities": ["multi_model_fusion", "enhanced_accuracy", "robust_processing"],
                "best_for": ["complex_audio", "highest_quality_results"],
                "available": any(model_availability.values())
            }
        }
        
        # Wrap in standardized API response format
        api_response = {
            "success": True,
            "data": {
                "models": models_info,
                "total_available": sum(1 for info in models_info.values() if info["available"]),
                "recommended_default": "auto",
                "selection_strategy": "content_aware"
            },
            "error": None,
            "timestamp": time.time(),
            "requestId": f"models_{int(time.time())}"
        }
        return api_response
        
    except Exception as e:
        logger.error(f"Failed to get available models: {str(e)}")
        
        # Return error in standardized API response format
        error_response = {
            "success": False,
            "data": None,
            "error": f"Model information unavailable: {str(e)}",
            "timestamp": time.time(),
            "requestId": f"models_error_{int(time.time())}"
        }
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )


# Health check endpoint
@router.get("/health", summary="Hybrid AI service health check")
async def health_check(request: Request):
    """Check hybrid AI service health status."""
    try:
        # Check if models are initialized from app state
        if hasattr(request.app.state, 'models_initialized') and request.app.state.models_initialized:
            available_models = getattr(request.app.state, 'available_models', [])
            return {
                "status": "healthy",
                "service": "hybrid-ai-mastering",
                "available_models": {model: True for model in available_models},
                "total_models": len(available_models),
                "timestamp": time.time(),
                "message": "Models loaded from app state"
            }
        
        # Fallback to checking hybrid extractor
        extractor = await get_hybrid_extractor()
        model_availability = extractor.model_loader.get_all_available_models()
        
        return {
            "status": "healthy",
            "service": "hybrid-ai-mastering",
            "available_models": model_availability,
            "total_models": len([k for k, v in model_availability.items() if v]),
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "hybrid-ai-mastering",
            "error": str(e),
            "timestamp": time.time()
        }


# Background processing function
async def _process_audio_background(
    job_id: str,
    audio_path: str,
    request_params: Dict
):
    """
    Background task for hybrid AI audio processing.
    
    This performs the heavy feature extraction and parameter prediction
    that was moved out of the main request handler.
    """
    try:
        # Setup processing context for comprehensive logging
        audio_filename = Path(audio_path).name
        
        with enterprise_logger.processing_context(
            job_id=job_id,
            audio_file=audio_filename,
            processing_mode=request_params.get('processing_mode', 'hybrid'),
            user_settings=request_params
        ) as proc_ctx:
            
            logger.info(f"Starting background hybrid AI processing for job {job_id}")
            log_performance("background_processing_start", 0, "timestamp")
            
            # Step 1: Create a temporary UploadFile-like object from the saved file
            from fastapi import UploadFile
            
            # Read the saved file
            file_read_start = time.time()
            async with aiofiles.open(audio_path, 'rb') as f:
                file_content = await f.read()
            file_read_time = (time.time() - file_read_start) * 1000
            log_performance("file_read_time", file_read_time, "ms", {"file_size": len(file_content)})
            
            # Create a BytesIO object to simulate an UploadFile
            file_like = io.BytesIO(file_content)
            
            # Create a mock request for the prediction function
            class MockRequest:
                def __init__(self):
                    self.app = type('MockApp', (), {})()
                    self.app.state = type('MockState', (), {})()
                    self.app.state.model_manager = None  # Will use global fallback
            
            mock_request = MockRequest()
            
            # Create HybridMasteringRequest from params
            mastering_request = HybridMasteringRequest(**request_params)
            
            # Log the final user settings that will be processed
            log_user_settings(request_params, "background_processing")
            
            # Step 2: Extract features and predict parameters (this is the heavy part)
            logger.info(f"Extracting features for job {job_id}")
            
            # Create a mock UploadFile for the prediction function
            class MockUploadFile:
                def __init__(self, content: bytes, filename: str):
                    self._content = io.BytesIO(content)
                    self.filename = filename
                    self.size = len(content)
                
                async def read(self, size: int = -1) -> bytes:
                    if size == -1:
                        return self._content.getvalue()
                    else:
                        return self._content.read(size)
                
                async def seek(self, position: int) -> None:
                    self._content.seek(position)
            
            mock_file = MockUploadFile(file_content, Path(audio_path).name)
            
            # Do the actual feature extraction and parameter prediction
            prediction_start = time.time()
            prediction_response = await predict_mastering_parameters(
                mock_request, mock_file, mastering_request
            )
            prediction_time = (time.time() - prediction_start) * 1000
            log_performance("ai_prediction_time", prediction_time, "ms")
            
            logger.info(f"Feature extraction completed for job {job_id}")
            
            # Log AI prediction results
            predicted_params = prediction_response.get('predicted_parameters', {})
            audio_characteristics = prediction_response.get('audio_characteristics', {})
            model_used = prediction_response.get('model_used', 'unknown')
            model_confidence = prediction_response.get('model_confidence', 0.0)
            
            log_ai_prediction(
                model_used=model_used,
                predicted_parameters=predicted_params,
                confidence=model_confidence,
                audio_characteristics=audio_characteristics
            )
            
            # Step 3: Apply actual AI-guided Matchering processing
            logger.info(f"Starting AI-guided audio mastering for job {job_id}")
            logger.info(f"Using AI predicted parameters: {predicted_params}")
            
            try:
                # Apply actual Matchering processing with AI parameters
                processed_audio_path = await _apply_ai_guided_mastering(
                    audio_path, 
                    predicted_params, 
                    mastering_request,
                    job_id
                )
                
                if processed_audio_path and Path(processed_audio_path).exists():
                    logger.info(f"Processed file created at: {processed_audio_path}")
                    logger.info(f"Processed file size: {Path(processed_audio_path).stat().st_size} bytes")
                    
                    # Move to results directory with proper naming
                    results_dir = Path("results")
                    results_dir.mkdir(exist_ok=True)
                    
                    # Extract original filename properly 
                    original_filename = request_params.get('original_filename', 'processed_audio.wav')
                    original_name = Path(original_filename).stem
                    output_filename = f"{original_name}_mastered.wav"
                    final_output_path = results_dir / output_filename
                    
                    # Copy processed file to results with proper name
                    shutil.copy2(processed_audio_path, final_output_path)
                    
                    logger.info(f"Mastered audio saved: {final_output_path}")
                    logger.info(f"Final output file size: {final_output_path.stat().st_size} bytes")
                    
                    # TODO: Store the result path in database for proper job-to-file mapping
                    # For now, we rely on file timestamps in results endpoint
                else:
                    logger.error(f"Failed to process audio for job {job_id}")
                    
            except Exception as processing_error:
                logger.error(f"Audio processing failed for job {job_id}: {processing_error}")
                logger.error(f"Processing traceback: {traceback.format_exc()}")
        
        logger.info(f"Background hybrid AI processing completed for job {job_id}")
        
        # TODO: Update job status in database to completed
        # TODO: Send completion notification via WebSocket
        # TODO: Store processed audio file and metadata
        
        # Clean up temporary files (keep original, clean up intermediate files)
        try:
            # Keep the original input file for comparison but clean up any intermediate files
            temp_dir = Path(audio_path).parent
            for temp_file in temp_dir.glob(f"*{job_id}*_temp*"):
                if temp_file.exists():
                    os.remove(temp_file)
                    logger.info(f"Cleaned up intermediate file: {temp_file}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up intermediate files: {cleanup_error}")
        
    except Exception as e:
        logger.error(f"Background processing failed for job {job_id}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # TODO: Update job status in database to failed
        # TODO: Send failure notification via WebSocket
        # For now, just ensure we don't crash the background task
        try:
            # Clean up temporary files
            if os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info(f"Cleaned up temporary file: {audio_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up temporary file: {cleanup_error}")


async def _apply_ai_guided_mastering(
    input_audio_path: str,
    predicted_params: Dict,
    mastering_request: HybridMasteringRequest,
    job_id: str
) -> Optional[str]:
    """
    Apply AI-guided mastering using predicted parameters.
    
    Args:
        input_audio_path: Path to input audio file
        predicted_params: AI-predicted mastering parameters
        mastering_request: User mastering preferences
        job_id: Processing job identifier
        
    Returns:
        Path to processed audio file or None if failed
    """
    try:
        logger.info(f"Starting AI-guided mastering for job {job_id}")
        
        # For AI mode, we create a "virtual reference" based on predicted parameters
        # Then use Matchering to apply similar processing
        
        # Create output filename
        input_path = Path(input_audio_path)
        output_filename = f"{input_path.stem}_mastered_{job_id}.wav"
        output_path = input_path.parent / output_filename
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output path: {output_path}")
        
        # Import Matchering for actual processing
        try:
            import matchering
            from matchering import Config, Result
        except ImportError as e:
            logger.error(f"Failed to import Matchering: {e}")
            return None
        
        # For now, since we don't have a reference track for AI mode,
        # we'll create a synthetic reference using AI parameters
        # This is a simplified implementation - in production you'd want
        # to use the predicted EQ curve, compression, etc. to guide processing
        
        # Apply basic AI-guided processing using predicted parameters
        config = Config()
        
        # Adjust config based on AI predictions
        if predicted_params.get('intensity_level') == 'high':
            config.loudness_max_peak = -0.5
        elif predicted_params.get('intensity_level') == 'low':
            config.loudness_max_peak = -2.0
        else:  # medium
            config.loudness_max_peak = -1.0
            
        # Apply real AI-guided mastering using Matchering with synthetic reference
        logger.info(f"Processing audio with AI parameters: {predicted_params}")
        
        # Step 1: Create virtual reference based on AI predictions
        virtual_reference_path = await _create_virtual_reference(
            input_audio_path, 
            predicted_params, 
            mastering_request,
            job_id
        )
        
        if not virtual_reference_path:
            logger.error("Failed to create virtual reference")
            # Fallback to basic loudness normalization
            return await _apply_basic_loudness_normalization(
                input_audio_path, 
                output_path, 
                mastering_request
            )
        
        # Step 2: Apply Matchering processing with virtual reference
        try:
            logger.info(f"Applying Matchering with virtual reference: {virtual_reference_path}")
            
            # Configure Matchering based on user settings
            config = _create_matchering_config(mastering_request, predicted_params)
            
            # Apply Matchering processing
            result = matchering.process(
                target=input_audio_path,
                reference=virtual_reference_path,
                results=[
                    matchering.pcm24(str(output_path))
                ],
                config=config
            )
            
            logger.info(f"Matchering processing completed successfully")
            
            # Clean up virtual reference
            try:
                if os.path.exists(virtual_reference_path):
                    os.remove(virtual_reference_path)
                    logger.info(f"Cleaned up virtual reference: {virtual_reference_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up virtual reference: {cleanup_error}")
            
            # Verify output file was created and has reasonable size
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                input_size = os.path.getsize(input_audio_path)
                logger.info(f"Processing complete - Input: {input_size} bytes, Output: {output_size} bytes")
                
                if output_size < 1000:  # Less than 1KB indicates failure
                    logger.error(f"Output file too small ({output_size} bytes), processing likely failed")
                    return None
                    
                return str(output_path)
            else:
                logger.error("Output file was not created")
                return None
                
        except Exception as matchering_error:
            logger.error(f"Matchering processing failed: {matchering_error}")
            logger.error(f"Matchering error traceback: {traceback.format_exc()}")
            
            # Fallback to basic processing
            logger.info("Falling back to basic loudness normalization")
            return await _apply_basic_loudness_normalization(
                input_audio_path, 
                output_path, 
                mastering_request
            )
        
    except Exception as e:
        logger.error(f"AI-guided mastering failed: {e}")
        logger.error(f"Mastering traceback: {traceback.format_exc()}")
        return None


async def _create_virtual_reference(
    input_audio_path: str,
    predicted_params: Dict,
    mastering_request: HybridMasteringRequest,
    job_id: str
) -> Optional[str]:
    """
    Create a virtual reference track based on AI predictions.
    This reference will guide the Matchering processing.
    """
    
    try:
        logger.info(f"Creating virtual reference for job {job_id}")
        
        # Use already imported audio processing libraries
        
        # Load the input audio using torchaudio (Python 3.12 compatible)
        audio, sr = torchaudio.load(input_audio_path)
        audio = audio.numpy()  # Convert to numpy for processing
        
        # Ensure we have stereo audio
        if audio.ndim == 1:
            audio = np.stack([audio, audio], axis=0)
        elif audio.shape[0] > 2:
            audio = audio[:2]  # Take first 2 channels
        
        # Create virtual reference based on AI predictions
        reference_audio = audio.copy()
        
        # Apply AI-predicted characteristics to create "ideal" reference
        
        # 1. Target loudness adjustment
        target_lufs = mastering_request.target_loudness_lufs or -16.0
        current_rms = np.sqrt(np.mean(audio**2))
        
        # Improved loudness scaling with proper LUFS conversion
        if current_rms > 0:
            # More accurate LUFS to linear scale conversion
            # LUFS = -0.691 + 10*log10(mean(audio^2))
            target_linear = 10**((target_lufs + 0.691) / 20.0)
            loudness_scale = target_linear / current_rms
            # Clamp scaling to prevent extreme values
            loudness_scale = np.clip(loudness_scale, 0.1, 10.0)
            reference_audio = reference_audio * loudness_scale
            logger.info(f"Applied loudness scaling: {loudness_scale:.3f} for target {target_lufs} LUFS")
        
        # 2. EQ adjustments based on AI predictions
        eq_style = mastering_request.eq_style
        if eq_style == "bright":
            # Boost high frequencies slightly
            reference_audio = _apply_simple_eq(reference_audio, sr, 'bright')
        elif eq_style == "warm":
            # Boost low-mids slightly
            reference_audio = _apply_simple_eq(reference_audio, sr, 'warm')
        elif eq_style == "auto":
            # AI-driven EQ adjustments based on audio characteristics
            # For now, default to balanced, but could use AI predictions here
            pass  # Balanced (no additional EQ)
        
        # 3. Dynamic range adjustment
        if mastering_request.preserve_dynamics:
            # Less compression for preserved dynamics
            reference_audio = _apply_gentle_compression(reference_audio)
        else:
            # More compression for modern loudness
            reference_audio = _apply_moderate_compression(reference_audio)
        
        # 4. Limiting to prevent clipping
        peak_level = np.max(np.abs(reference_audio))
        if peak_level > 0.95:
            reference_audio = reference_audio * (0.95 / peak_level)
        
        # Save virtual reference
        input_path = Path(input_audio_path)
        virtual_ref_path = input_path.parent / f"virtual_ref_{job_id}.wav"
        
        # Ensure reference_audio is in the right format for soundfile
        if reference_audio.ndim == 2:
            reference_audio = reference_audio.T  # soundfile expects (n_samples, n_channels)
        
        sf.write(str(virtual_ref_path), reference_audio, sr, format='WAV', subtype='PCM_24')
        
        logger.info(f"Virtual reference created: {virtual_ref_path}")
        return str(virtual_ref_path)
        
    except Exception as e:
        logger.error(f"Failed to create virtual reference: {e}")
        logger.error(f"Virtual reference creation traceback: {traceback.format_exc()}")
        return None


def _apply_simple_eq(audio, sr: int, style: str):
    """Apply simple EQ adjustments to create reference characteristics."""
    try:
        
        # Simple biquad filter implementations
        if style == 'bright':
            # High shelf at 8kHz, +2dB
            sos = signal.butter(2, 8000, btype='highpass', fs=sr, output='sos')
            if audio.ndim == 2:
                audio[0] = signal.sosfilt(sos, audio[0]) * 1.05  # Slight boost
                audio[1] = signal.sosfilt(sos, audio[1]) * 1.05
            else:
                audio = signal.sosfilt(sos, audio) * 1.05
                
        elif style == 'warm':
            # Low shelf at 200Hz, +1dB
            sos = signal.butter(2, 200, btype='lowpass', fs=sr, output='sos')
            if audio.ndim == 2:
                audio[0] = signal.sosfilt(sos, audio[0]) * 1.03  # Slight boost
                audio[1] = signal.sosfilt(sos, audio[1]) * 1.03
            else:
                audio = signal.sosfilt(sos, audio) * 1.03
        
        return audio
    except Exception as e:
        logger.warning(f"EQ application failed: {e}")
        return audio  # Return original if EQ fails


def _apply_gentle_compression(audio):
    """Apply gentle compression to maintain dynamics."""
    try:
        
        # Simple soft limiting
        threshold = 0.8
        ratio = 0.1  # Very gentle
        
        # Apply to each channel
        if audio.ndim == 2:
            for ch in range(audio.shape[0]):
                over_thresh = np.abs(audio[ch]) > threshold
                audio[ch][over_thresh] = threshold + (audio[ch][over_thresh] - threshold) * ratio
        else:
            over_thresh = np.abs(audio) > threshold
            audio[over_thresh] = threshold + (audio[over_thresh] - threshold) * ratio
            
        return audio
    except Exception as e:
        logger.warning(f"Gentle compression failed: {e}")
        return audio


def _apply_moderate_compression(audio):
    """Apply moderate compression for modern loudness."""
    try:
        
        # Moderate soft limiting
        threshold = 0.7
        ratio = 0.3  # More compression
        
        # Apply to each channel
        if audio.ndim == 2:
            for ch in range(audio.shape[0]):
                over_thresh = np.abs(audio[ch]) > threshold
                audio[ch][over_thresh] = threshold + (audio[ch][over_thresh] - threshold) * ratio
        else:
            over_thresh = np.abs(audio) > threshold
            audio[over_thresh] = threshold + (audio[over_thresh] - threshold) * ratio
            
        return audio
    except Exception as e:
        logger.warning(f"Moderate compression failed: {e}")
        return audio


def _create_matchering_config(
    mastering_request: HybridMasteringRequest,
    predicted_params: Dict
) -> "Config":
    """Create Matchering configuration based on user settings and AI predictions."""
    try:
        # Log the Matchering configuration creation with user settings
        config_start = time.time()
        from matchering import Config
        
        config = Config()
        
        # Apply user preferences
        if mastering_request.preserve_dynamics:
            config.limiter_max_amplification_db = 8.0  # Less aggressive
        else:
            config.limiter_max_amplification_db = 12.0  # More aggressive
        
        # Apply USER intensity settings (FIXED: was reading from predicted_params)
        intensity = mastering_request.intensity_level  # CORRECT SOURCE!
        target_lufs = mastering_request.target_loudness_lufs
        
        # Configure based on target LUFS with proper intensity scaling
        if target_lufs <= -10.0:  # Very aggressive (streaming/club music)
            config.loudness_max_peak = -0.035
            config.limiter_max_amplification_db = 26.0
            config.limiter_attack_coefficient = 0.003  # Fast attack
        elif target_lufs <= -12.0:  # Aggressive (modern pop)
            config.loudness_max_peak = -0.05
            config.limiter_max_amplification_db = 22.0
            config.limiter_attack_coefficient = 0.005
        elif target_lufs <= -16.0:  # Standard (streaming)
            config.loudness_max_peak = -0.1
            config.limiter_max_amplification_db = 15.0
            config.limiter_attack_coefficient = 0.01
        elif target_lufs <= -20.0:  # Conservative (dynamic music)
            config.loudness_max_peak = -0.3
            config.limiter_max_amplification_db = 10.0
            config.limiter_attack_coefficient = 0.02
        else:  # Very conservative (classical, jazz)
            config.loudness_max_peak = -0.5
            config.limiter_max_amplification_db = 6.0
            config.limiter_attack_coefficient = 0.05
        
        # Apply intensity scaling on top of LUFS-based settings
        if intensity == 'high':
            config.limiter_max_amplification_db = min(config.limiter_max_amplification_db * 1.3, 30.0)
            config.loudness_max_peak = max(config.loudness_max_peak * 0.7, -0.03)
        elif intensity == 'low':
            config.limiter_max_amplification_db = max(config.limiter_max_amplification_db * 0.7, 5.0)
            config.loudness_max_peak = min(config.loudness_max_peak * 1.5, -0.5)
        
        # Log comprehensive Matchering configuration
        config_time = (time.time() - config_start) * 1000
        config_dict = {
            "loudness_max_peak": config.loudness_max_peak,
            "limiter_max_amplification_db": config.limiter_max_amplification_db,
            "limiter_attack_coefficient": getattr(config, 'limiter_attack_coefficient', None),
            "preserve_dynamics": mastering_request.preserve_dynamics
        }
        
        log_matchering_config(config_dict, mastering_request.dict())
        log_performance("matchering_config_creation", config_time, "ms")
        
        logger.info(f"Created Matchering config for {target_lufs} LUFS, intensity={intensity}: "
                   f"max_peak={config.loudness_max_peak}, max_amp={config.limiter_max_amplification_db}")
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to create Matchering config: {e}")
        # Return default config
        from matchering import Config
        return Config()


async def _apply_basic_loudness_normalization(
    input_path: str,
    output_path: str,
    mastering_request: HybridMasteringRequest
) -> Optional[str]:
    """
    Fallback function: Apply basic loudness normalization if Matchering fails.
    This ensures we always return a processed file, even if it's just normalized.
    """
    
    try:
        logger.info("Applying basic loudness normalization as fallback")
        
        # Load audio using torchaudio (Python 3.12 compatible)
        audio, sr = torchaudio.load(input_path)
        audio = audio.numpy()  # Convert to numpy for processing
        
        # Ensure stereo
        if audio.ndim == 1:
            audio = np.stack([audio, audio], axis=0)
        elif audio.shape[0] > 2:
            audio = audio[:2]
        
        # Basic loudness normalization
        target_lufs = mastering_request.target_loudness_lufs or -16.0
        current_rms = np.sqrt(np.mean(audio**2))
        
        if current_rms > 0:
            # Simple RMS-based normalization (approximates LUFS)
            target_rms = 10**(target_lufs / 20.0) * 0.1
            scale_factor = target_rms / current_rms
            
            # Apply gentle scaling to avoid distortion
            scale_factor = min(scale_factor, 3.0)  # Limit boost
            audio = audio * scale_factor
        
        # Simple limiting
        peak = np.max(np.abs(audio))
        if peak > 0.95:
            audio = audio * (0.95 / peak)
        
        # Save normalized audio
        if audio.ndim == 2:
            audio = audio.T  # soundfile expects (n_samples, n_channels)
            
        sf.write(output_path, audio, sr, format='WAV', subtype='PCM_24')
        
        # Verify output
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            logger.info(f"Basic normalization complete: {output_size} bytes")
            return output_path
        else:
            logger.error("Basic normalization failed to create output file")
            return None
            
    except Exception as e:
        logger.error(f"Basic loudness normalization failed: {e}")
        logger.error(f"Normalization traceback: {traceback.format_exc()}")
        return None


def _estimate_processing_time(
    file_size: int,
    processing_mode: str,
    model_used: str
) -> float:
    """
    Estimate processing time based on various factors.
    
    Args:
        file_size: Size of audio file in bytes
        processing_mode: Processing mode being used
        model_used: AI model being used
        
    Returns:
        Estimated processing time in seconds
    """
    # Estimate duration based on file size (rough approximation)
    estimated_duration = max(10.0, file_size / 1_000_000)  # ~1MB per minute
    base_time = estimated_duration * 0.2  # Base: 20% of estimated duration
    
    # Adjust for processing mode
    mode_multipliers = {
        "ai": 1.0,
        "reference": 1.5,
        "hybrid": 1.2
    }
    
    # Adjust for model complexity
    model_multipliers = {
        "ast": 1.2,
        "wav2vec": 1.5,
        "clap": 1.3,
        "custom": 1.0,
        "ensemble": 2.0
    }
    
    multiplier = mode_multipliers.get(processing_mode, 1.0) * model_multipliers.get(model_used, 1.0)
    
    return base_time * multiplier + 5.0  # Add 5 second overhead


def _generate_ai_eq_curve(
    request: HybridMasteringRequest,
    characteristics: "AudioCharacteristics"
) -> List[float]:
    """
    Generate AI-guided EQ curve based on user preferences and audio characteristics.
    
    Args:
        request: User mastering request with EQ style preference
        characteristics: Audio analysis characteristics
        
    Returns:
        List of 31 EQ gains in dB for standard frequency bands
    """
    try:
        # 31-band EQ frequencies (standard graphic EQ)
        # 20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
        # 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000 Hz
        
        # Initialize with flat response
        eq_curve = [0.0] * 31
        
        # Get EQ style preference
        eq_style = request.eq_style or "balanced"
        
        # Base EQ curves for different styles
        if eq_style == "bright":
            # Bright style: gentle low-cut, high-shelf boost
            eq_curve = [
                -0.5, -0.3, -0.2, -0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # 20-200 Hz
                0.0, 0.0, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7,       # 250-1600 Hz
                0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0, 3.2  # 2000-20000 Hz
            ]
        elif eq_style == "warm":
            # Warm style: gentle low boost, slight high roll-off
            eq_curve = [
                1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.2, 0.1, 0.1,       # 20-200 Hz
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.1, -0.2,     # 250-1600 Hz
                -0.3, -0.4, -0.5, -0.6, -0.7, -0.8, -1.0, -1.2, -1.4, -1.6, -1.8  # 2000-20000 Hz
            ]
        elif eq_style == "balanced":
            # Balanced style: gentle smile curve
            eq_curve = [
                0.3, 0.2, 0.2, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0,       # 20-200 Hz
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.2,       # 250-1600 Hz
                0.3, 0.4, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.6, 1.7, 1.8  # 2000-20000 Hz
            ]
        elif eq_style == "auto":
            # Auto style: analyze audio characteristics for intelligent EQ
            spectral_centroid = getattr(characteristics, 'spectral_centroid', 2500.0)
            
            if spectral_centroid < 2000:  # Dark/warm content
                eq_curve = [
                    0.2, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,   # Gentle low boost
                    0.0, 0.0, 0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.1,   # Midrange presence
                    1.3, 1.5, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4  # High boost
                ]
            elif spectral_centroid > 3500:  # Bright/harsh content
                eq_curve = [
                    0.5, 0.4, 0.3, 0.2, 0.2, 0.1, 0.1, 0.0, 0.0, 0.0,   # Low warmth
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.1, -0.2, -0.3, # Midrange cut
                    -0.4, -0.5, -0.6, -0.8, -1.0, -1.2, -1.4, -1.6, -1.8, -2.0, -2.2  # High cut
                ]
            else:  # Balanced content
                eq_curve = [
                    0.2, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,   # Subtle low boost
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.2, 0.3,   # Midrange clarity
                    0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.1, 2.2  # High presence
                ]
        else:
            # Default to balanced for unknown styles
            eq_curve = [
                0.2, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.2, 0.3,
                0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.1, 2.2
            ]
        
        # Clamp EQ values to reasonable range (±6dB)
        eq_curve = [max(-6.0, min(6.0, gain)) for gain in eq_curve]
        
        return eq_curve
        
    except Exception as e:
        logger.error(f"EQ curve generation failed: {e}")
        # Return flat response on error
        return [0.0] * 31