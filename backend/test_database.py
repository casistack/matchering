#!/usr/bin/env python3
"""
Database operation testing script for Enhanced Matchering API.

This script tests database connectivity, model operations, and validation.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add the app directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_db, engine
from app.models.audio import AudioFile, AudioMetadata
from app.models.processing import ProcessingJob, JobProgress, JobStatus, ProcessingMode, ProcessingStage


async def test_database_connection():
    """Test basic database connectivity."""
    print("🔗 Testing database connection...")
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(select(1))
            assert result.scalar() == 1
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_audio_models():
    """Test AudioFile and AudioMetadata model operations."""
    print("\n🎵 Testing audio models...")
    
    try:
        async for session in get_db():
            # Create test audio file with unique identifiers
            test_id = str(uuid.uuid4()).replace('-', '')[:8]
            audio_file = AudioFile(
                id=uuid.uuid4(),
                filename=f"test_audio_{test_id}.wav",
                original_filename=f"test_original_{test_id}.wav", 
                file_path=f"/uploads/test_audio_{test_id}.wav",
                file_size=1024000,
                mime_type="audio/wav",
                checksum=f"test_checksum_{test_id}",
                format="wav",
                sample_rate=44100,
                bit_depth=16,
                channels=2,
                duration=120.5,
                processing_eligible=True
            )
            
            session.add(audio_file)
            await session.commit()
            
            # Create audio metadata
            metadata = AudioMetadata(
                id=uuid.uuid4(),
                audio_file_id=audio_file.id,
                rms_level=-12.5,
                peak_level=-3.2,
                dynamic_range=8.7,
                spectral_centroid=2500.0,
                lufs_integrated=-14.2,
                mfcc_features={"mean": [1.2, 3.4, 5.6], "std": [0.1, 0.2, 0.3]},
                analysis_version="1.0.0"
            )
            
            session.add(metadata)
            await session.commit()
            
            # Query and verify
            result = await session.execute(
                select(AudioFile).where(AudioFile.id == audio_file.id)
            )
            retrieved_file = result.scalar_one_or_none()
            
            assert retrieved_file is not None
            assert retrieved_file.filename == f"test_audio_{test_id}.wav"
            assert retrieved_file.sample_rate == 44100
            
            # Query metadata
            result = await session.execute(
                select(AudioMetadata).where(AudioMetadata.audio_file_id == audio_file.id)
            )
            retrieved_metadata = result.scalar_one_or_none()
            
            assert retrieved_metadata is not None
            assert retrieved_metadata.rms_level == -12.5
            assert retrieved_metadata.mfcc_features["mean"] == [1.2, 3.4, 5.6]
            
            print("✅ Audio models test successful")
            return True
            
    except Exception as e:
        print(f"❌ Audio models test failed: {e}")
        return False


async def test_processing_models():
    """Test ProcessingJob and JobProgress model operations."""
    print("\n⚙️ Testing processing models...")
    
    try:
        async for session in get_db():
            # Create test processing job
            job = ProcessingJob(
                id=uuid.uuid4(),
                input_file_id=uuid.uuid4(),  # Would reference an actual audio file
                processing_mode=ProcessingMode.AUTO,
                settings={"quality": "high", "loudness_target": -14.0},
                status=JobStatus.PENDING,
                priority=5,
                progress_percentage=0.0,
                retry_count=0
            )
            
            session.add(job)
            await session.commit()
            
            # Create job progress
            progress = JobProgress(
                id=uuid.uuid4(),
                job_id=job.id,
                stage=ProcessingStage.VALIDATION,
                progress_percentage=25.0,
                message="File validation completed",
                stage_started_at=datetime.utcnow(),
                details={"files_checked": 1, "validation_time": 0.5}
            )
            
            session.add(progress)
            await session.commit()
            
            # Update job status
            job.status = JobStatus.PROCESSING
            job.current_stage = ProcessingStage.FEATURE_EXTRACTION
            job.progress_percentage = 25.0
            await session.commit()
            
            # Query and verify
            result = await session.execute(
                select(ProcessingJob).where(ProcessingJob.id == job.id)
            )
            retrieved_job = result.scalar_one_or_none()
            
            assert retrieved_job is not None
            assert retrieved_job.status == JobStatus.PROCESSING
            assert retrieved_job.processing_mode == ProcessingMode.AUTO
            assert retrieved_job.settings["quality"] == "high"
            
            # Query progress
            result = await session.execute(
                select(JobProgress).where(JobProgress.job_id == job.id)
            )
            retrieved_progress = result.scalar_one_or_none()
            
            assert retrieved_progress is not None
            assert retrieved_progress.stage == ProcessingStage.VALIDATION
            assert retrieved_progress.progress_percentage == 25.0
            assert retrieved_progress.details["files_checked"] == 1
            
            print("✅ Processing models test successful")
            return True
            
    except Exception as e:
        print(f"❌ Processing models test failed: {e}")
        return False


async def test_enum_operations():
    """Test enum field operations."""
    print("\n🔢 Testing enum operations...")
    
    try:
        # Test all job statuses
        statuses = [
            JobStatus.PENDING,
            JobStatus.QUEUED,
            JobStatus.PROCESSING,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED
        ]
        
        for status in statuses:
            assert isinstance(status.value, str)
        
        # Test processing modes
        modes = [
            ProcessingMode.AUTO,
            ProcessingMode.REFERENCE,
            ProcessingMode.HYBRID
        ]
        
        for mode in modes:
            assert isinstance(mode.value, str)
        
        # Test processing stages
        stages = [
            ProcessingStage.VALIDATION,
            ProcessingStage.FEATURE_EXTRACTION,
            ProcessingStage.AI_ANALYSIS,
            ProcessingStage.PARAMETER_PREDICTION,
            ProcessingStage.AUDIO_PROCESSING,
            ProcessingStage.QUALITY_CHECK,
            ProcessingStage.FINALIZATION
        ]
        
        for stage in stages:
            assert isinstance(stage.value, str)
        
        print("✅ Enum operations test successful")
        return True
        
    except Exception as e:
        print(f"❌ Enum operations test failed: {e}")
        return False


async def test_json_field_operations():
    """Test JSON field storage and retrieval."""
    print("\n📄 Testing JSON field operations...")
    
    try:
        async for session in get_db():
            # Test complex JSON data
            complex_settings = {
                "processing": {
                    "quality": "high",
                    "loudness_target": -14.0,
                    "dynamics": {
                        "compressor": {"ratio": 3.0, "attack": 0.003, "release": 0.1},
                        "limiter": {"ceiling": -0.1, "release": 0.05}
                    }
                },
                "features": ["spectral_matching", "dynamic_processing"],
                "metadata": {"version": "2.0", "timestamp": "2025-06-29T04:20:00Z"}
            }
            
            job = ProcessingJob(
                id=uuid.uuid4(),
                input_file_id=uuid.uuid4(),
                processing_mode=ProcessingMode.AUTO,
                settings=complex_settings,
                status=JobStatus.PENDING,
                priority=5,
                progress_percentage=0.0,
                retry_count=0
            )
            
            session.add(job)
            await session.commit()
            
            # Retrieve and verify JSON data
            result = await session.execute(
                select(ProcessingJob).where(ProcessingJob.id == job.id)
            )
            retrieved_job = result.scalar_one_or_none()
            
            assert retrieved_job is not None
            assert retrieved_job.settings["processing"]["quality"] == "high"
            assert retrieved_job.settings["processing"]["dynamics"]["compressor"]["ratio"] == 3.0
            assert "spectral_matching" in retrieved_job.settings["features"]
            
            print("✅ JSON field operations test successful")
            return True
            
    except Exception as e:
        print(f"❌ JSON field operations test failed: {e}")
        return False


async def cleanup_test_data():
    """Clean up test data from database."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        from sqlalchemy import text
        
        async for session in get_db():
            # Delete all test data using text() for raw SQL
            await session.execute(text("DELETE FROM job_progress"))
            await session.execute(text("DELETE FROM processing_jobs"))  
            await session.execute(text("DELETE FROM audio_metadata"))
            await session.execute(text("DELETE FROM audio_files"))
            await session.commit()
            
        print("✅ Test data cleanup successful")
        return True
        
    except Exception as e:
        print(f"❌ Test data cleanup failed: {e}")
        return False


async def main():
    """Run all database tests."""
    print("🚀 Starting database operation tests...\n")
    
    tests = [
        test_database_connection,
        test_enum_operations,
        test_audio_models,
        test_processing_models,
        test_json_field_operations,
        cleanup_test_data
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if await test():
            passed += 1
        else:
            break  # Stop on first failure
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All database tests completed successfully!")
        return True
    else:
        print("💥 Some tests failed. Check the database configuration and models.")
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    exit(0 if success else 1)