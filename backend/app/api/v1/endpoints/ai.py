"""
AI processing endpoints for audio mastering.

This module provides FastAPI endpoints for AI-powered audio analysis
and mastering parameter prediction.
"""

import asyncio
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.feature_extractor import AudioFeatures, create_feature_extractor
from app.core.database import get_db
from app.schemas.ai import (
    AudioFeaturesResponse,
    FeatureExtractionRequest,
    FeatureExtractionResponse,
    PerformanceStatsResponse,
)
from app.services.ai_service import get_ai_service
from app.utils.file_utils import save_uploaded_file, validate_audio_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Processing"])

# Global feature extractor instance
feature_extractor = create_feature_extractor()


@router.post(
    "/extract-features",
    response_model=FeatureExtractionResponse,
    summary="Extract audio features for AI analysis",
    description="Extract comprehensive audio features including MFCC, spectral, and harmonic features for AI mastering analysis."
)
async def extract_audio_features(
    file: UploadFile = File(..., description="Audio file to analyze"),
    analysis_depth: str = "full",
    cache_result: bool = True,
    db: AsyncSession = Depends(get_db)
) -> FeatureExtractionResponse:
    """
    Extract comprehensive audio features for AI analysis.
    
    This endpoint processes uploaded audio files and extracts features
    used by AI models for mastering parameter prediction.
    
    Args:
        file: Audio file (WAV, MP3, FLAC supported)
        analysis_depth: Analysis depth ("fast", "standard", "full")
        cache_result: Whether to cache extracted features
        db: Database session
        
    Returns:
        FeatureExtractionResponse with extracted features and metadata
    """
    start_time = time.time()
    
    try:
        # Validate audio file
        if not validate_audio_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid audio file format. Supported: WAV, MP3, FLAC"
            )
        
        # Check file size (limit to 100MB for performance)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size: 100MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Save uploaded file temporarily
        temp_file_path = await save_uploaded_file(file)
        
        logger.info(f"Starting feature extraction for {file.filename} ({file_size / 1024 / 1024:.1f}MB)")
        
        # Configure feature extractor based on analysis depth
        extractor_config = _get_extractor_config(analysis_depth)
        configured_extractor = create_feature_extractor(extractor_config)
        
        # Extract features
        audio_features = await configured_extractor.extract_features(temp_file_path)
        
        # Store features in cache if requested
        if cache_result:
            ai_service = get_ai_service()
            await ai_service.cache_features(audio_features.feature_hash, audio_features)
        
        # Calculate processing metrics
        processing_time = time.time() - start_time
        
        # Create response
        response = FeatureExtractionResponse(
            success=True,
            features=AudioFeaturesResponse(
                feature_hash=audio_features.feature_hash,
                extraction_time=audio_features.extraction_time,
                sample_rate=audio_features.sample_rate,
                duration=audio_features.duration,
                channels=audio_features.channels,
                mfcc_shape=(len(audio_features.mfcc), len(audio_features.mfcc[0]) if audio_features.mfcc else 0),
                spectral_features_count=len(audio_features.spectral_centroid),
                chroma_shape=(len(audio_features.chroma), len(audio_features.chroma[0]) if audio_features.chroma else 0),
                mastering_features={
                    "dynamic_range": audio_features.dynamic_range,
                    "loudness_lufs": audio_features.loudness_lufs,
                    "peak_level": audio_features.peak_level,
                    "crest_factor": audio_features.crest_factor,
                    "stereo_width": audio_features.stereo_width,
                    "tempo": audio_features.tempo
                }
            ),
            processing_time=processing_time,
            file_info={
                "filename": file.filename,
                "size_mb": file_size / 1024 / 1024,
                "analysis_depth": analysis_depth
            }
        )
        
        logger.info(f"Feature extraction completed in {processing_time:.3f}s for {file.filename}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feature extraction failed for {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature extraction failed: {str(e)}"
        )


@router.get(
    "/features/{feature_hash}",
    response_model=AudioFeaturesResponse,
    summary="Retrieve cached audio features",
    description="Retrieve previously extracted audio features using the feature hash."
)
async def get_cached_features(
    feature_hash: str,
    include_raw_features: bool = False
) -> AudioFeaturesResponse:
    """
    Retrieve cached audio features by hash.
    
    Args:
        feature_hash: Hash identifier for cached features
        include_raw_features: Whether to include raw feature arrays
        
    Returns:
        AudioFeaturesResponse with cached features
    """
    try:
        ai_service = get_ai_service()
        cached_features = await ai_service.get_cached_features(feature_hash)
        
        if not cached_features:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Features not found for hash: {feature_hash}"
            )
        
        # Create response (optionally excluding raw arrays for performance)
        response = AudioFeaturesResponse(
            feature_hash=cached_features.feature_hash,
            extraction_time=cached_features.extraction_time,
            sample_rate=cached_features.sample_rate,
            duration=cached_features.duration,
            channels=cached_features.channels,
            mfcc_shape=(len(cached_features.mfcc), len(cached_features.mfcc[0]) if cached_features.mfcc else 0),
            spectral_features_count=len(cached_features.spectral_centroid),
            chroma_shape=(len(cached_features.chroma), len(cached_features.chroma[0]) if cached_features.chroma else 0),
            mastering_features={
                "dynamic_range": cached_features.dynamic_range,
                "loudness_lufs": cached_features.loudness_lufs,
                "peak_level": cached_features.peak_level,
                "crest_factor": cached_features.crest_factor,
                "stereo_width": cached_features.stereo_width,
                "tempo": cached_features.tempo
            }
        )
        
        # Include raw features if requested
        if include_raw_features:
            response.raw_features = cached_features
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve cached features {feature_hash}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cached features: {str(e)}"
        )


@router.post(
    "/analyze-batch",
    response_model=list[FeatureExtractionResponse],
    summary="Batch audio feature extraction",
    description="Extract features from multiple audio files in a single request."
)
async def extract_features_batch(
    files: list[UploadFile] = File(..., description="Audio files to analyze"),
    analysis_depth: str = "standard",
    max_concurrent: int = 3
) -> list[FeatureExtractionResponse]:
    """
    Extract features from multiple audio files concurrently.
    
    Args:
        files: List of audio files to analyze
        analysis_depth: Analysis depth for all files
        max_concurrent: Maximum concurrent extractions
        
    Returns:
        List of FeatureExtractionResponse objects
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per batch request"
        )
    
    # Create semaphore to limit concurrent processing
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single_file(file: UploadFile) -> FeatureExtractionResponse:
        async with semaphore:
            # Create a new UploadFile instance for each concurrent task
            file_content = await file.read()
            await file.seek(0)
            
            # Process the file
            return await extract_audio_features(file, analysis_depth, cache_result=True)
    
    try:
        # Process files concurrently
        tasks = [process_single_file(file) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch processing failed for file {i}: {str(result)}")
                # Create error response
                responses.append(FeatureExtractionResponse(
                    success=False,
                    error=str(result),
                    processing_time=0.0,
                    file_info={"filename": files[i].filename if i < len(files) else "unknown"}
                ))
            else:
                responses.append(result)
        
        return responses
        
    except Exception as e:
        logger.error(f"Batch feature extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing failed: {str(e)}"
        )


@router.get(
    "/performance-stats",
    response_model=PerformanceStatsResponse,
    summary="Get feature extraction performance statistics",
    description="Retrieve performance metrics for the feature extraction service."
)
async def get_performance_stats() -> PerformanceStatsResponse:
    """
    Get performance statistics for feature extraction.
    
    Returns:
        PerformanceStatsResponse with timing and throughput metrics
    """
    try:
        stats = feature_extractor.get_performance_stats()
        
        # Get additional service stats
        ai_service = get_ai_service()
        cache_stats = await ai_service.get_cache_stats()
        
        return PerformanceStatsResponse(
            extraction_stats=stats,
            cache_stats=cache_stats,
            service_uptime=time.time() - _service_start_time,
            total_extractions=stats.get('total_extractions', 0)
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance stats: {str(e)}"
        )


@router.delete(
    "/cache/{feature_hash}",
    summary="Delete cached features",
    description="Remove cached features from the feature store."
)
async def delete_cached_features(feature_hash: str) -> JSONResponse:
    """
    Delete cached features by hash.
    
    Args:
        feature_hash: Hash identifier for cached features
        
    Returns:
        Success message
    """
    try:
        ai_service = get_ai_service()
        deleted = await ai_service.delete_cached_features(feature_hash)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Features not found for hash: {feature_hash}"
            )
        
        return JSONResponse(
            content={"message": f"Features deleted successfully: {feature_hash}"},
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete cached features {feature_hash}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cached features: {str(e)}"
        )


def _get_extractor_config(analysis_depth: str) -> dict:
    """Get feature extractor configuration based on analysis depth."""
    
    configs = {
        "fast": {
            "hop_length": 1024,  # Larger hop for faster processing
            "n_mfcc": 13,
            "n_chroma": 12
        },
        "standard": {
            "hop_length": 512,   # Standard hop length
            "n_mfcc": 13,
            "n_chroma": 12
        },
        "full": {
            "hop_length": 256,   # Smaller hop for detailed analysis
            "n_mfcc": 20,        # More MFCC coefficients
            "n_chroma": 12
        }
    }
    
    return configs.get(analysis_depth, configs["standard"])


# Service startup time for uptime calculation
_service_start_time = time.time()


# Health check endpoint
@router.get("/health", summary="AI service health check")
async def health_check():
    """Check AI service health status."""
    return {
        "status": "healthy",
        "service": "ai-feature-extraction",
        "uptime": time.time() - _service_start_time,
        "timestamp": time.time()
    }