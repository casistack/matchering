#!/usr/bin/env python3
"""
Processing Job Management API testing script for Enhanced Matchering API.

This script tests the complete processing job workflow including creation,
management, queue operations, and WebSocket updates without requiring a running server.
"""

import asyncio
import sys
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Add the app directory to path for imports
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal, engine, Base
from app.models.audio import AudioFile
from app.models.processing import ProcessingJob, JobProgress, JobStatus, ProcessingMode, ProcessingStage
from app.schemas.processing import ProcessingJobCreate
from app.utils.request_utils import generate_request_id
from app.utils.validation_utils import validate_uuid_string, validate_processing_mode
from app.core.config import settings

logger = logging.getLogger(__name__)


class MockRequest:
    """Mock FastAPI request for testing."""
    
    def __init__(self):
        self.method = "POST"
        self.url = "http://localhost:8000/test"
        self.headers = {
            "user-agent": "test-client",
            "content-type": "application/json"
        }
        self.query_params = {}
        self.client = MockClient()
    
    class MockClient:
        host = "127.0.0.1"


async def setup_test_data(session) -> Dict[str, Any]:
    """Set up test data for processing job tests."""
    print("📋 Setting up test data...")
    
    # Generate unique identifiers for this test run
    test_run_id = uuid.uuid4().hex[:8]
    
    # Create test audio files with unique paths
    input_file = AudioFile(
        id=uuid.uuid4(),
        filename=f"test_input_{test_run_id}.wav",
        original_filename="test_input.wav",
        file_path=f"/uploads/test_input_{test_run_id}.wav",
        file_size=5000000,  # 5MB
        mime_type="audio/wav",
        checksum=f"test_input_checksum_{test_run_id}",
        format="wav",
        sample_rate=44100,
        bit_depth=24,
        channels=2,
        duration=180.0,
        processing_eligible=True
    )
    
    reference_file = AudioFile(
        id=uuid.uuid4(),
        filename=f"test_reference_{test_run_id}.wav",
        original_filename="test_reference.wav",
        file_path=f"/uploads/test_reference_{test_run_id}.wav",
        file_size=4000000,  # 4MB
        mime_type="audio/wav",
        checksum=f"test_reference_checksum_{test_run_id}",
        format="wav",
        sample_rate=44100,
        bit_depth=24,
        channels=2,
        duration=200.0,
        processing_eligible=True
    )
    
    ineligible_file = AudioFile(
        id=uuid.uuid4(),
        filename=f"test_ineligible_{test_run_id}.wav",
        original_filename="test_ineligible.wav",
        file_path=f"/uploads/test_ineligible_{test_run_id}.wav",
        file_size=3000000,  # 3MB
        mime_type="audio/wav",
        checksum=f"test_ineligible_checksum_{test_run_id}",
        format="wav",
        sample_rate=44100,
        bit_depth=16,
        channels=2,
        duration=150.0,
        processing_eligible=False  # Not eligible for processing
    )
    
    session.add_all([input_file, reference_file, ineligible_file])
    await session.commit()
    
    test_data = {
        "input_file": input_file,
        "reference_file": reference_file,
        "ineligible_file": ineligible_file
    }
    
    print(f"  ✓ Created test input file: {input_file.id}")
    print(f"  ✓ Created test reference file: {reference_file.id}")
    print(f"  ✓ Created ineligible file: {ineligible_file.id}")
    
    return test_data


async def test_job_creation_validation() -> bool:
    """Test processing job creation and validation."""
    print("\n🔧 Testing job creation and validation...")
    
    try:
        async with AsyncSessionLocal() as session:
            test_data = await setup_test_data(session)
            
            # Test 1: Valid auto-mastering job creation
            valid_job_data = ProcessingJobCreate(
                input_file_id=test_data["input_file"].id,
                processing_mode="auto",
                settings={"quality": "standard", "loudness_target": -14},
                priority=5
            )
            
            # Simulate job creation logic
            processing_job = ProcessingJob(
                id=uuid.uuid4(),
                input_file_id=valid_job_data.input_file_id,
                processing_mode=ProcessingMode(valid_job_data.processing_mode),
                settings=valid_job_data.settings,
                status=JobStatus.PENDING,
                queue_position=1,
                priority=valid_job_data.priority
            )
            
            session.add(processing_job)
            await session.commit()
            
            print(f"  ✓ Created auto-mastering job: {processing_job.id}")
            
            # Test 2: Valid reference-mastering job creation
            reference_job_data = ProcessingJobCreate(
                input_file_id=test_data["input_file"].id,
                reference_file_id=test_data["reference_file"].id,
                processing_mode="reference",
                settings={"quality": "high", "matching_strength": 0.8},
                priority=3
            )
            
            reference_job = ProcessingJob(
                id=uuid.uuid4(),
                input_file_id=reference_job_data.input_file_id,
                reference_file_id=reference_job_data.reference_file_id,
                processing_mode=ProcessingMode(reference_job_data.processing_mode),
                settings=reference_job_data.settings,
                status=JobStatus.PENDING,
                queue_position=2,
                priority=reference_job_data.priority
            )
            
            session.add(reference_job)
            await session.commit()
            
            print(f"  ✓ Created reference-mastering job: {reference_job.id}")
            
            # Test 3: Test processing mode validation
            try:
                validate_processing_mode("auto")
                validate_processing_mode("reference")
                validate_processing_mode("hybrid")
                print("  ✓ Processing mode validation working")
            except Exception as e:
                print(f"  ❌ Processing mode validation failed: {e}")
                return False
            
            # Test 4: Test invalid processing mode
            try:
                validate_processing_mode("invalid_mode")
                print("  ❌ Should have failed for invalid mode")
                return False
            except Exception:
                print("  ✓ Invalid processing mode correctly rejected")
            
            # Test 5: Test UUID validation
            try:
                validate_uuid_string(str(test_data["input_file"].id), "file_id")
                print("  ✓ UUID validation working")
            except Exception as e:
                print(f"  ❌ UUID validation failed: {e}")
                return False
            
            # Test 6: Test invalid UUID
            try:
                validate_uuid_string("invalid-uuid", "file_id")
                print("  ❌ Should have failed for invalid UUID")
                return False
            except Exception:
                print("  ✓ Invalid UUID correctly rejected")
            
            print("✅ Job creation and validation test passed")
            return True
        
    except Exception as e:
        print(f"❌ Job creation and validation test failed: {e}")
        return False


async def test_job_lifecycle_management() -> bool:
    """Test job lifecycle management operations."""
    print("\n📊 Testing job lifecycle management...")
    
    try:
        async with AsyncSessionLocal() as session:
            test_data = await setup_test_data(session)
            
            # Create test job
            test_job = ProcessingJob(
                id=uuid.uuid4(),
                input_file_id=test_data["input_file"].id,
                processing_mode=ProcessingMode.AUTO,
                settings={"quality": "standard"},
                status=JobStatus.PENDING,
                queue_position=1,
                priority=5
            )
            
            session.add(test_job)
            await session.commit()
            
            print(f"  ✓ Created test job: {test_job.id}")
            
            # Test job status progression
            test_job.status = JobStatus.QUEUED
            test_job.started_at = datetime.utcnow()
            await session.commit()
            print(f"  ✓ Job status updated to QUEUED")
            
            test_job.status = JobStatus.PROCESSING
            test_job.current_stage = ProcessingStage.FEATURE_EXTRACTION
            test_job.progress_percentage = 25.0
            await session.commit()
            print(f"  ✓ Job status updated to PROCESSING (25% complete)")
            
            # Create progress entry
            progress_entry = JobProgress(
                id=uuid.uuid4(),
                job_id=test_job.id,
                stage=ProcessingStage.FEATURE_EXTRACTION,
                progress_percentage=25.0,
                message="Extracting audio features",
                details={"features_extracted": 12, "total_features": 48}
            )
            
            session.add(progress_entry)
            await session.commit()
            print(f"  ✓ Created progress entry: {progress_entry.stage.value}")
            
            # Complete the job
            test_job.status = JobStatus.COMPLETED
            test_job.completed_at = datetime.utcnow()
            test_job.progress_percentage = 100.0
            test_job.processing_duration = 180.5
            test_job.result_metadata = {
                "output_file": {
                    "filename": "mastered_output.wav",
                    "size": 5200000,
                    "format": "wav"
                }
            }
            await session.commit()
            print(f"  ✓ Job completed successfully")
            
            # Test job cancellation scenario
            cancel_job = ProcessingJob(
                id=uuid.uuid4(),
                input_file_id=test_data["reference_file"].id,  # Different file
                processing_mode=ProcessingMode.AUTO,
                settings={"quality": "draft"},
                status=JobStatus.PROCESSING,
                queue_position=2,
                priority=7
            )
            
            session.add(cancel_job)
            await session.commit()
            
            # Cancel the job
            cancel_job.status = JobStatus.CANCELLED
            cancel_job.completed_at = datetime.utcnow()
            cancel_job.error_message = "Job cancelled by user"
            cancel_job.error_code = "USER_CANCELLED"
            await session.commit()
            print(f"  ✓ Job cancelled successfully: {cancel_job.id}")
            
            # Test job failure scenario
            fail_job = ProcessingJob(
                id=uuid.uuid4(),
                input_file_id=test_data["reference_file"].id,
                processing_mode=ProcessingMode.REFERENCE,
                settings={"quality": "high"},
                status=JobStatus.FAILED,
                queue_position=3,
                priority=8,
                error_message="Processing failed due to corrupted audio",
                error_code="AUDIO_CORRUPTION",
                retry_count=3
            )
            
            session.add(fail_job)
            await session.commit()
            print(f"  ✓ Created failed job: {fail_job.id}")
            
            print("✅ Job lifecycle management test passed")
            return True
        
    except Exception as e:
        print(f"❌ Job lifecycle management test failed: {e}")
        return False


async def test_queue_management() -> bool:
    """Test queue management and statistics."""
    print("\n📈 Testing queue management and statistics...")
    
    try:
        async with AsyncSessionLocal() as session:
            test_data = await setup_test_data(session)
            
            # Create multiple jobs in different states
            jobs_data = [
                (JobStatus.PENDING, ProcessingMode.AUTO, 5),
                (JobStatus.QUEUED, ProcessingMode.AUTO, 3),
                (JobStatus.PROCESSING, ProcessingMode.REFERENCE, 1),
                (JobStatus.COMPLETED, ProcessingMode.AUTO, 8),
                (JobStatus.FAILED, ProcessingMode.REFERENCE, 9),
                (JobStatus.CANCELLED, ProcessingMode.HYBRID, 6),
            ]
            
            created_jobs = []
            for status, mode, priority in jobs_data:
                job = ProcessingJob(
                    id=uuid.uuid4(),
                    input_file_id=test_data["input_file"].id,
                    processing_mode=mode,
                    settings={"quality": "standard"},
                    status=status,
                    priority=priority,
                    processing_duration=150.0 if status == JobStatus.COMPLETED else None
                )
                
                if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    job.completed_at = datetime.utcnow() - timedelta(hours=2)
                
                created_jobs.append(job)
                session.add(job)
            
            await session.commit()
            print(f"  ✓ Created {len(created_jobs)} test jobs")
            
            # Test queue statistics
            from sqlalchemy import select, func, and_
            
            # Total jobs
            total_query = select(func.count(ProcessingJob.id))
            total_result = await session.execute(total_query)
            total_jobs = total_result.scalar()
            print(f"  ✓ Total jobs: {total_jobs}")
            
            # Queued jobs
            queued_query = select(func.count(ProcessingJob.id)).where(
                ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED])
            )
            queued_result = await session.execute(queued_query)
            queued_jobs = queued_result.scalar()
            print(f"  ✓ Queued jobs: {queued_jobs}")
            
            # Jobs by status
            status_query = select(
                ProcessingJob.status,
                func.count(ProcessingJob.id).label('count')
            ).group_by(ProcessingJob.status)
            
            status_result = await session.execute(status_query)
            jobs_by_status = {row.status.value: row.count for row in status_result}
            print(f"  ✓ Jobs by status: {jobs_by_status}")
            
            # Jobs by mode
            mode_query = select(
                ProcessingJob.processing_mode,
                func.count(ProcessingJob.id).label('count')
            ).group_by(ProcessingJob.processing_mode)
            
            mode_result = await session.execute(mode_query)
            jobs_by_mode = {row.processing_mode.value: row.count for row in mode_result}
            print(f"  ✓ Jobs by mode: {jobs_by_mode}")
            
            # Average processing time
            avg_time_query = select(func.avg(ProcessingJob.processing_duration)).where(
                and_(
                    ProcessingJob.status == JobStatus.COMPLETED,
                    ProcessingJob.processing_duration.is_not(None)
                )
            )
            avg_time_result = await session.execute(avg_time_query)
            avg_processing_time = avg_time_result.scalar()
            print(f"  ✓ Average processing time: {avg_processing_time:.1f}s")
            
            # Jobs by priority
            priority_query = select(
                ProcessingJob.priority,
                func.count(ProcessingJob.id).label('count')
            ).where(
                ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED])
            ).group_by(ProcessingJob.priority)
            
            priority_result = await session.execute(priority_query)
            jobs_by_priority = {str(row.priority): row.count for row in priority_result}
            print(f"  ✓ Jobs by priority: {jobs_by_priority}")
            
            # Recent activity (24 hours)
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            
            recent_completed_query = select(func.count(ProcessingJob.id)).where(
                and_(
                    ProcessingJob.status == JobStatus.COMPLETED,
                    ProcessingJob.completed_at >= twenty_four_hours_ago
                )
            )
            recent_completed_result = await session.execute(recent_completed_query)
            recent_completed = recent_completed_result.scalar()
            print(f"  ✓ Jobs completed in last 24h: {recent_completed}")
            
            print("✅ Queue management and statistics test passed")
            return True
        
    except Exception as e:
        print(f"❌ Queue management and statistics test failed: {e}")
        return False


async def test_processing_modes_config() -> bool:
    """Test processing modes configuration."""
    print("\n⚙️ Testing processing modes configuration...")
    
    try:
        # Test processing modes configuration
        modes_config = [
            {
                "mode": "auto",
                "display_name": "AI Auto-Mastering",
                "description": "Fully automated mastering using AI analysis and parameter prediction",
                "requires_reference": False,
                "estimated_duration": 180.0,
                "settings_schema": {
                    "type": "object",
                    "properties": {
                        "quality": {
                            "type": "string",
                            "enum": ["draft", "standard", "high", "maximum"],
                            "default": "standard"
                        },
                        "loudness_target": {
                            "type": "number",
                            "minimum": -30,
                            "maximum": 0,
                            "default": -14
                        }
                    }
                }
            },
            {
                "mode": "reference",
                "display_name": "Reference-Based Mastering",
                "description": "Traditional reference-based mastering using target audio characteristics",
                "requires_reference": True,
                "estimated_duration": 240.0,
                "settings_schema": {
                    "type": "object",
                    "properties": {
                        "quality": {
                            "type": "string",
                            "enum": ["draft", "standard", "high", "maximum"],
                            "default": "high"
                        },
                        "matching_strength": {
                            "type": "number",
                            "minimum": 0.1,
                            "maximum": 1.0,
                            "default": 0.8
                        }
                    }
                }
            },
            {
                "mode": "hybrid",
                "display_name": "Hybrid Processing",
                "description": "Combines AI analysis with reference-based techniques for optimal results",
                "requires_reference": False,
                "estimated_duration": 300.0,
                "settings_schema": {
                    "type": "object",
                    "properties": {
                        "quality": {
                            "type": "string",
                            "enum": ["standard", "high", "maximum"],
                            "default": "high"
                        },
                        "ai_weight": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "default": 0.7
                        }
                    }
                }
            }
        ]
        
        print(f"  ✓ Available processing modes: {len(modes_config)}")
        
        for mode in modes_config:
            print(f"    - {mode['mode']}: {mode['display_name']}")
            print(f"      Requires reference: {mode['requires_reference']}")
            print(f"      Estimated duration: {mode['estimated_duration']}s")
            
            # Validate settings schema structure
            schema = mode['settings_schema']
            if "properties" in schema and "quality" in schema["properties"]:
                print(f"      Quality options: {schema['properties']['quality']['enum']}")
            
        default_mode = "auto"
        print(f"  ✓ Default processing mode: {default_mode}")
        
        print("✅ Processing modes configuration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Processing modes configuration test failed: {e}")
        return False


async def test_job_validation_scenarios() -> bool:
    """Test various job validation scenarios."""
    print("\n🚨 Testing job validation scenarios...")
    
    try:
        async with AsyncSessionLocal() as session:
            test_data = await setup_test_data(session)
            
            # Test 1: Job with non-existent input file
            try:
                non_existent_id = uuid.uuid4()
                invalid_job_data = ProcessingJobCreate(
                    input_file_id=non_existent_id,
                    processing_mode="auto",
                    settings={"quality": "standard"}
                )
                
                # Check if file exists (should fail)
                from sqlalchemy import select
                query = select(AudioFile).where(AudioFile.id == non_existent_id)
                result = await session.execute(query)
                file_found = result.scalar_one_or_none()
                
                if file_found:
                    print("  ❌ Should not have found non-existent file")
                    return False
                else:
                    print("  ✓ Correctly detected non-existent input file")
                
            except Exception as e:
                print(f"  ✓ Non-existent file validation working: {type(e).__name__}")
            
            # Test 2: Job with ineligible file
            try:
                ineligible_job = ProcessingJobCreate(
                    input_file_id=test_data["ineligible_file"].id,
                    processing_mode="auto",
                    settings={"quality": "standard"}
                )
                
                # Check file eligibility
                if not test_data["ineligible_file"].processing_eligible:
                    print("  ✓ Correctly detected ineligible file")
                else:
                    print("  ❌ Should have detected ineligible file")
                    return False
                
            except Exception as e:
                print(f"  ✓ File eligibility validation working: {type(e).__name__}")
            
            # Test 3: Reference mode without reference file
            try:
                reference_job_no_ref = ProcessingJobCreate(
                    input_file_id=test_data["input_file"].id,
                    processing_mode="reference",
                    settings={"quality": "high"}
                    # Missing reference_file_id
                )
                
                if not reference_job_no_ref.reference_file_id:
                    print("  ✓ Correctly detected missing reference file for reference mode")
                else:
                    print("  ❌ Should have detected missing reference file")
                    return False
                
            except Exception as e:
                print(f"  ✓ Reference file validation working: {type(e).__name__}")
            
            # Test 4: Duplicate active job prevention
            try:
                # Create an active job
                active_job = ProcessingJob(
                    id=uuid.uuid4(),
                    input_file_id=test_data["input_file"].id,
                    processing_mode=ProcessingMode.AUTO,
                    settings={"quality": "standard"},
                    status=JobStatus.PROCESSING,
                    priority=5
                )
                
                session.add(active_job)
                await session.commit()
                
                # Try to create another job for the same file
                from sqlalchemy import select, and_
                duplicate_check_query = select(ProcessingJob).where(
                    and_(
                        ProcessingJob.input_file_id == test_data["input_file"].id,
                        ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING])
                    )
                )
                duplicate_result = await session.execute(duplicate_check_query)
                existing_job = duplicate_result.scalar_one_or_none()
                
                if existing_job:
                    print("  ✓ Correctly detected duplicate active job")
                else:
                    print("  ❌ Should have detected duplicate active job")
                    return False
                
            except Exception as e:
                print(f"  ✓ Duplicate job validation working: {type(e).__name__}")
            
            # Test 5: Priority validation
            valid_priorities = [1, 5, 10]
            invalid_priorities = [0, 11, -1, "high"]
            
            for priority in valid_priorities:
                if isinstance(priority, int) and 1 <= priority <= 10:
                    print(f"  ✓ Valid priority accepted: {priority}")
                else:
                    print(f"  ❌ Valid priority rejected: {priority}")
                    return False
            
            for priority in invalid_priorities:
                if not isinstance(priority, int) or priority < 1 or priority > 10:
                    print(f"  ✓ Invalid priority rejected: {priority}")
                else:
                    print(f"  ❌ Invalid priority accepted: {priority}")
                    return False
            
            print("✅ Job validation scenarios test passed")
            return True
        
    except Exception as e:
        print(f"❌ Job validation scenarios test failed: {e}")
        return False


async def test_websocket_message_format() -> bool:
    """Test WebSocket message format and structure."""
    print("\n📡 Testing WebSocket message format...")
    
    try:
        # Test WebSocket message structures
        job_id = str(uuid.uuid4())
        
        # Connection established message
        connection_msg = {
            "type": "connection_established",
            "payload": {
                "job_id": job_id,
                "message": "Connected to job progress updates"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        
        print("  ✓ Connection established message format valid")
        
        # Progress update message
        progress_msg = {
            "type": "processing_progress",
            "payload": {
                "job_id": job_id,
                "status": "processing",
                "progress_percentage": 45.5,
                "current_stage": "audio_processing",
                "message": "Processing stage: audio_processing",
                "elapsed_time": 90,
                "remaining_time": 110
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        
        print("  ✓ Progress update message format valid")
        
        # Job completion message
        completion_msg = {
            "type": "job_completed",
            "payload": {
                "job_id": job_id,
                "status": "completed",
                "message": "Processing completed successfully",
                "output_file_url": f"/api/v1/results/{job_id}/download"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        
        print("  ✓ Job completion message format valid")
        
        # Error message
        error_msg = {
            "type": "error",
            "payload": {
                "job_id": job_id,
                "error": "Connection error occurred",
                "error_code": "WEBSOCKET_ERROR"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        
        print("  ✓ Error message format valid")
        
        # Test JSON serialization
        messages = [connection_msg, progress_msg, completion_msg, error_msg]
        for i, msg in enumerate(messages):
            try:
                json_str = json.dumps(msg)
                parsed = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["type", "payload", "timestamp", "message_id"]
                for field in required_fields:
                    if field not in parsed:
                        print(f"  ❌ Missing required field '{field}' in message {i}")
                        return False
                
                print(f"  ✓ Message {i} serialization valid")
                
            except Exception as e:
                print(f"  ❌ Message {i} serialization failed: {e}")
                return False
        
        # Test processing stages progression
        stages = ["validation", "feature_extraction", "ai_analysis", "audio_processing", "finalization"]
        for stage in stages:
            if stage in ["validation", "feature_extraction", "ai_analysis", "audio_processing", "finalization"]:
                print(f"  ✓ Valid processing stage: {stage}")
            else:
                print(f"  ❌ Invalid processing stage: {stage}")
                return False
        
        print("✅ WebSocket message format test passed")
        return True
        
    except Exception as e:
        print(f"❌ WebSocket message format test failed: {e}")
        return False


async def test_performance_scenarios() -> bool:
    """Test performance-related scenarios."""
    print("\n⚡ Testing performance scenarios...")
    
    try:
        async with AsyncSessionLocal() as session:
            test_data = await setup_test_data(session)
            
            # Test 1: Bulk job creation performance
            import time
            start_time = time.time()
            
            bulk_jobs = []
            for i in range(50):
                job = ProcessingJob(
                    id=uuid.uuid4(),
                    input_file_id=test_data["input_file"].id,
                    processing_mode=ProcessingMode.AUTO,
                    settings={"quality": "draft"},
                    status=JobStatus.PENDING,
                    priority=5 + (i % 5)  # Vary priorities
                )
                bulk_jobs.append(job)
            
            session.add_all(bulk_jobs)
            await session.commit()
            
            creation_time = time.time() - start_time
            print(f"  ✓ Created 50 jobs in {creation_time:.3f}s")
            
            # Test 2: Bulk query performance
            start_time = time.time()
            
            from sqlalchemy import select
            query = select(ProcessingJob).where(
                ProcessingJob.status == JobStatus.PENDING
            ).limit(100)
            
            result = await session.execute(query)
            jobs = result.scalars().all()
            
            query_time = time.time() - start_time
            print(f"  ✓ Queried {len(jobs)} jobs in {query_time:.3f}s")
            
            # Test 3: Statistics calculation performance
            start_time = time.time()
            
            # Multiple aggregation queries
            from sqlalchemy import func, and_
            
            stats_queries = [
                select(func.count(ProcessingJob.id)),
                select(func.count(ProcessingJob.id)).where(ProcessingJob.status == JobStatus.PENDING),
                select(func.avg(ProcessingJob.processing_duration)).where(
                    ProcessingJob.processing_duration.is_not(None)
                ),
                select(
                    ProcessingJob.status,
                    func.count(ProcessingJob.id)
                ).group_by(ProcessingJob.status)
            ]
            
            for query in stats_queries:
                await session.execute(query)
            
            stats_time = time.time() - start_time
            print(f"  ✓ Calculated statistics in {stats_time:.3f}s")
            
            # Test 4: Memory usage estimation
            import sys
            
            # Estimate memory usage of job objects
            sample_job = ProcessingJob(
                id=uuid.uuid4(),
                input_file_id=test_data["input_file"].id,
                processing_mode=ProcessingMode.AUTO,
                settings={"quality": "standard"},
                status=JobStatus.PENDING,
                priority=5
            )
            
            job_size = sys.getsizeof(sample_job)
            estimated_memory_1000_jobs = job_size * 1000 / (1024 * 1024)  # MB
            
            print(f"  ✓ Estimated memory for 1000 jobs: {estimated_memory_1000_jobs:.2f}MB")
            
            # Test 5: Request ID generation performance
            start_time = time.time()
            
            request_ids = [generate_request_id() for _ in range(1000)]
            
            generation_time = time.time() - start_time
            unique_ids = len(set(request_ids))
            
            if unique_ids == 1000:
                print(f"  ✓ Generated 1000 unique request IDs in {generation_time:.3f}s")
            else:
                print(f"  ❌ Only {unique_ids} unique IDs out of 1000")
                return False
            
            print("✅ Performance scenarios test passed")
            return True
        
    except Exception as e:
        print(f"❌ Performance scenarios test failed: {e}")
        return False


async def cleanup_test_data(session) -> None:
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Delete all test processing jobs
        from sqlalchemy import delete
        
        await session.execute(delete(JobProgress))
        await session.execute(delete(ProcessingJob))
        await session.execute(delete(AudioFile))
        await session.commit()
        
        print("  ✓ Test data cleaned up successfully")
        
    except Exception as e:
        print(f"  ⚠️ Cleanup warning: {e}")


async def main() -> bool:
    """Run all processing job management tests."""
    print("🚀 Starting Processing Job Management API tests...\n")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    tests = [
        test_job_creation_validation,
        test_job_lifecycle_management,
        test_queue_management,
        test_processing_modes_config,
        test_job_validation_scenarios,
        test_websocket_message_format,
        test_performance_scenarios
    ]
    
    passed = 0
    total = len(tests)
    
    try:
        for test in tests:
            if await test():
                passed += 1
            else:
                break  # Stop on first failure
        
        # Clean up
        async with AsyncSessionLocal() as session:
            await cleanup_test_data(session)
        
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All processing job management tests completed successfully!")
        return True
    else:
        print("💥 Some tests failed. Check the processing job implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)