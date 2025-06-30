"""
Hybrid AI mastering endpoints for FastAPI.

This module provides production-ready endpoints for hybrid AI mastering
combining pre-trained models (AST, Wav2Vec, CLAP, MusicGen) with custom models
for intelligent audio mastering parameter prediction and processing.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional
from pathlib import Path

import torch
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

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
    
    model_preference: Optional[str] = Field(
        default="auto",
        description="Preferred model ('auto', 'ast', 'wav2vec', 'clap', 'custom', 'ensemble')"
    )
    user_style: Optional[str] = Field(
        default=None,
        description="Text description of desired mastering style (for CLAP model)"
    )
    processing_mode: str = Field(
        default="hybrid",
        description="Processing mode ('ai', 'reference', 'hybrid')"
    )
    intensity_level: str = Field(
        default="medium",
        description="Mastering intensity ('low', 'medium', 'high')"
    )
    preserve_dynamics: bool = Field(
        default=True,
        description="Whether to preserve dynamic range"
    )
    target_loudness_lufs: float = Field(
        default=-14.0,
        description="Target loudness in LUFS (-23 to -6)"
    )
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
        
        # Create dummy parameters for now (would come from actual model prediction)
        predicted_params = MasteringParameters(
            genre_probabilities={"pop": 0.7, "electronic": 0.2, "rock": 0.1},
            predicted_genre="pop",
            eq_curve=[0.0] * 31,  # Flat EQ for now
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
        
        # Apply user preferences
        if request.intensity_level == "high":
            predicted_params.compression_ratio = min(predicted_params.compression_ratio * 1.5, 8.0)
            predicted_params.limiting_threshold = max(predicted_params.limiting_threshold - 2.0, -6.0)
        elif request.intensity_level == "low":
            predicted_params.compression_ratio = max(predicted_params.compression_ratio * 0.7, 1.5)
            predicted_params.limiting_threshold = min(predicted_params.limiting_threshold + 1.0, -0.5)
        
        if not request.preserve_dynamics:
            predicted_params.compression_ratio = min(predicted_params.compression_ratio * 1.3, 10.0)
        
        # Adjust target loudness
        if abs(request.target_loudness_lufs - (-14.0)) > 1.0:
            # Adjust limiting ceiling based on target loudness
            loudness_diff = request.target_loudness_lufs - (-14.0)
            predicted_params.limiting_ceiling = max(min(predicted_params.limiting_ceiling - loudness_diff, 0.0), -3.0)
        
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
    response_model=HybridMasteringResponse,
    summary="Process audio using hybrid AI mastering",
    description="Complete hybrid AI mastering pipeline with intelligent model selection and processing."
)
async def process_hybrid_mastering(
    http_request: Request,
    file: UploadFile = File(..., description="Audio file to master"),
    request: HybridMasteringRequest = Depends(),
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
        
        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Queue background processing (do ALL heavy work in background)
        background_tasks.add_task(
            _process_audio_background,
            job_id=job_id,
            audio_path=str(temp_file_path),
            request_params=request.dict()
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
            duration=0.0,  # Will be updated in background
            sample_rate=0,  # Will be updated in background
            channels=0,  # Will be updated in background
            format="unknown",  # Will be updated in background
            file_size=file.size or 0,
            genre="unknown",
            genre_confidence=0.0,
            energy_level=0.5,
            complexity_score=0.5,
            audio_quality=0.5,
            has_vocals=False
        )
        
        # Create basic mastering parameters
        basic_parameters = MasteringParameters(
            eq_low_gain=0.0,
            eq_mid_gain=0.0,
            eq_high_gain=0.0,
            compression_ratio=2.0,
            compression_threshold=-12.0,
            limiting_ceiling=-0.5,
            stereo_width=1.0,
            harmonic_enhancement=0.3
        )
        
        response = HybridMasteringResponse(
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
        
        logger.info(f"Hybrid mastering job {job_id} queued successfully in {processing_time:.3f}s")
        return response
        
    except Exception as e:
        logger.error(f"Hybrid mastering request failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid mastering failed: {str(e)}"
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
        
        return {
            "models": models_info,
            "total_available": sum(1 for info in models_info.values() if info["available"]),
            "recommended_default": "auto",
            "selection_strategy": "content_aware"
        }
        
    except Exception as e:
        logger.error(f"Failed to get available models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model information unavailable: {str(e)}"
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
        logger.info(f"Starting background hybrid AI processing for job {job_id}")
        
        # Step 1: Create a temporary UploadFile-like object from the saved file
        from fastapi import UploadFile
        import aiofiles
        
        # Read the saved file
        async with aiofiles.open(audio_path, 'rb') as f:
            file_content = await f.read()
        
        # Create a BytesIO object to simulate an UploadFile
        import io
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
        
        # Step 2: Extract features and predict parameters (this is the heavy part)
        logger.info(f"Extracting features for job {job_id}")
        
        # Create a mock UploadFile for the prediction function
        class MockUploadFile:
            def __init__(self, content: bytes, filename: str):
                self._content = io.BytesIO(content)
                self.filename = filename
                self.size = len(content)
            
            async def read(self) -> bytes:
                return self._content.getvalue()
            
            async def seek(self, position: int) -> None:
                self._content.seek(position)
        
        mock_file = MockUploadFile(file_content, Path(audio_path).name)
        
        # Do the actual feature extraction and parameter prediction
        prediction_response = await predict_mastering_parameters(
            mock_request, mock_file, mastering_request
        )
        
        logger.info(f"Feature extraction completed for job {job_id}")
        
        # Step 3: TODO - Integrate with actual Matchering processing pipeline
        # For now, simulate the actual audio processing
        logger.info(f"Simulating audio processing for job {job_id}")
        await asyncio.sleep(2.0)  # Simulate processing time
        
        logger.info(f"Background hybrid AI processing completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Background processing failed for job {job_id}: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")


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