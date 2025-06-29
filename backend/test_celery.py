#!/usr/bin/env python3
"""
Celery configuration and task testing script for Enhanced Matchering API.

This script tests Celery configuration, task registration, and basic functionality
without requiring a running Redis broker.
"""

import sys
import uuid
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add the app directory to path for imports
sys.path.append(str(Path(__file__).parent))

from app.core.celery_app import celery_app, health_check
from app.workers import audio_tasks, analysis_tasks, file_tasks, maintenance_tasks

logger = logging.getLogger(__name__)


def test_celery_configuration() -> bool:
    """Test Celery application configuration."""
    print("🔧 Testing Celery configuration...")
    
    try:
        # Test basic configuration
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert celery_app.conf.task_default_queue == "matchering_default"
        
        # Test broker and backend URLs
        broker_url = celery_app.conf.broker_url
        result_backend = celery_app.conf.result_backend
        
        assert broker_url is not None
        assert result_backend is not None
        assert "redis://" in broker_url
        assert "redis://" in result_backend
        
        # Test task routing
        routes = celery_app.conf.task_routes
        assert "app.workers.audio_tasks.*" in routes
        assert routes["app.workers.audio_tasks.*"]["queue"] == "audio_processing"
        
        # Test worker configuration
        assert celery_app.conf.worker_prefetch_multiplier == 1
        assert celery_app.conf.worker_max_tasks_per_child == 50
        assert celery_app.conf.task_acks_late is True
        
        print("✅ Celery configuration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Celery configuration test failed: {e}")
        return False


def test_task_registration() -> bool:
    """Test that all tasks are properly registered."""
    print("\n📋 Testing task registration...")
    
    try:
        # Get all registered tasks
        registered_tasks = celery_app.tasks
        
        expected_tasks = [
            # Core tasks
            "health_check",
            
            # Audio processing tasks
            "process_audio_auto_master",
            "process_audio_reference_master",
            
            # Analysis tasks
            "analyze_audio_file",
            "extract_audio_features",
            
            # File management tasks
            "validate_uploaded_file",
            "cleanup_temporary_files",
            "archive_processed_files",
            
            # Maintenance tasks
            "cleanup_old_results",
            "update_job_metrics",
            "cleanup_orphaned_files",
            "update_processing_estimates"
        ]
        
        missing_tasks = []
        for task_name in expected_tasks:
            if task_name not in registered_tasks:
                missing_tasks.append(task_name)
        
        if missing_tasks:
            print(f"❌ Missing tasks: {missing_tasks}")
            return False
        
        print(f"✅ All {len(expected_tasks)} tasks properly registered")
        
        # Test task routing
        routing_tests = [
            ("process_audio_auto_master", "audio_processing"),
            ("analyze_audio_file", "audio_analysis"),
            ("validate_uploaded_file", "file_operations"),
            ("cleanup_old_results", "matchering_default")
        ]
        
        for task_name, expected_queue in routing_tests:
            task = registered_tasks[task_name]
            route_info = celery_app.conf.task_routes.get(f"app.workers.{task_name.split('_')[0]}_tasks.*")
            if route_info and route_info.get("queue") == expected_queue:
                print(f"  ✓ {task_name} -> {expected_queue}")
            elif expected_queue == "matchering_default":
                print(f"  ✓ {task_name} -> {expected_queue} (default)")
            else:
                print(f"  ⚠️ {task_name} routing may be incorrect")
        
        return True
        
    except Exception as e:
        print(f"❌ Task registration test failed: {e}")
        return False


def test_task_signatures() -> bool:
    """Test task signatures and basic validation."""
    print("\n📝 Testing task signatures...")
    
    try:
        # Test health check task (can run without broker)
        health_task = celery_app.tasks["health_check"]
        assert health_task is not None
        
        # Test that health_check function exists and is callable
        result = health_check()
        assert isinstance(result, dict)
        assert "status" in result
        assert "timestamp" in result
        assert result["status"] == "healthy"
        
        print("  ✓ health_check task signature valid")
        
        # Test audio processing task signatures
        audio_tasks_to_test = [
            "process_audio_auto_master",
            "process_audio_reference_master"
        ]
        
        for task_name in audio_tasks_to_test:
            task = celery_app.tasks[task_name]
            assert task is not None
            assert hasattr(task, 'apply_async')
            print(f"  ✓ {task_name} signature valid")
        
        # Test analysis task signatures
        analysis_tasks_to_test = [
            "analyze_audio_file",
            "extract_audio_features"
        ]
        
        for task_name in analysis_tasks_to_test:
            task = celery_app.tasks[task_name]
            assert task is not None
            assert hasattr(task, 'apply_async')
            print(f"  ✓ {task_name} signature valid")
        
        # Test file task signatures
        file_tasks_to_test = [
            "validate_uploaded_file",
            "cleanup_temporary_files",
            "archive_processed_files"
        ]
        
        for task_name in file_tasks_to_test:
            task = celery_app.tasks[task_name]
            assert task is not None
            assert hasattr(task, 'apply_async')
            print(f"  ✓ {task_name} signature valid")
        
        # Test maintenance task signatures
        maintenance_tasks_to_test = [
            "cleanup_old_results",
            "update_job_metrics",
            "cleanup_orphaned_files",
            "update_processing_estimates"
        ]
        
        for task_name in maintenance_tasks_to_test:
            task = celery_app.tasks[task_name]
            assert task is not None
            assert hasattr(task, 'apply_async')
            print(f"  ✓ {task_name} signature valid")
        
        print("✅ All task signatures valid")
        return True
        
    except Exception as e:
        print(f"❌ Task signature test failed: {e}")
        return False


def test_task_queues_configuration() -> bool:
    """Test task queue configuration."""
    print("\n🚦 Testing task queue configuration...")
    
    try:
        # Test queue routing configuration
        routes = celery_app.conf.task_routes
        
        expected_routes = {
            "app.workers.audio_tasks.*": {"queue": "audio_processing"},
            "app.workers.analysis_tasks.*": {"queue": "audio_analysis"},
            "app.workers.file_tasks.*": {"queue": "file_operations"},
        }
        
        for pattern, expected_config in expected_routes.items():
            if pattern in routes:
                if routes[pattern] == expected_config:
                    print(f"  ✓ {pattern} -> {expected_config['queue']}")
                else:
                    print(f"  ❌ {pattern} routing incorrect: {routes[pattern]}")
                    return False
            else:
                print(f"  ❌ Missing route for {pattern}")
                return False
        
        # Test default queue
        default_queue = celery_app.conf.task_default_queue
        assert default_queue == "matchering_default"
        print(f"  ✓ Default queue: {default_queue}")
        
        print("✅ Task queue configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ Task queue configuration test failed: {e}")
        return False


def test_beat_schedule() -> bool:
    """Test Celery Beat periodic task schedule."""
    print("\n⏰ Testing Celery Beat schedule...")
    
    try:
        schedule = celery_app.conf.beat_schedule
        
        expected_scheduled_tasks = [
            "cleanup_old_results",
            "update_job_metrics"
        ]
        
        for task_name in expected_scheduled_tasks:
            if task_name not in schedule:
                print(f"  ❌ Missing scheduled task: {task_name}")
                return False
            
            task_config = schedule[task_name]
            assert "task" in task_config
            assert "schedule" in task_config
            assert isinstance(task_config["schedule"], (int, float))
            
            print(f"  ✓ {task_name}: every {task_config['schedule']} seconds")
        
        # Test timezone setting
        timezone = celery_app.conf.timezone
        assert timezone == "UTC"
        print(f"  ✓ Timezone: {timezone}")
        
        print("✅ Beat schedule configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ Beat schedule test failed: {e}")
        return False


def test_worker_configuration() -> bool:
    """Test worker-specific configuration."""
    print("\n👷 Testing worker configuration...")
    
    try:
        conf = celery_app.conf
        
        # Test worker limits
        assert conf.worker_prefetch_multiplier == 1
        print(f"  ✓ Prefetch multiplier: {conf.worker_prefetch_multiplier}")
        
        assert conf.worker_max_tasks_per_child == 50
        print(f"  ✓ Max tasks per child: {conf.worker_max_tasks_per_child}")
        
        # Test task execution settings
        assert conf.task_acks_late is True
        print(f"  ✓ Late acknowledgment: {conf.task_acks_late}")
        
        assert conf.task_reject_on_worker_lost is True
        print(f"  ✓ Reject on worker lost: {conf.task_reject_on_worker_lost}")
        
        # Test time limits
        assert conf.task_soft_time_limit == 300
        print(f"  ✓ Soft time limit: {conf.task_soft_time_limit}s")
        
        assert conf.task_time_limit == 600
        print(f"  ✓ Hard time limit: {conf.task_time_limit}s")
        
        # Test monitoring
        assert conf.worker_send_task_events is True
        print(f"  ✓ Send task events: {conf.worker_send_task_events}")
        
        print("✅ Worker configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ Worker configuration test failed: {e}")
        return False


def test_import_validation() -> bool:
    """Test that all task modules can be imported without errors."""
    print("\n📦 Testing task module imports...")
    
    try:
        # Test direct imports
        import app.workers.audio_tasks
        print("  ✓ audio_tasks module imported")
        
        import app.workers.analysis_tasks
        print("  ✓ analysis_tasks module imported")
        
        import app.workers.file_tasks
        print("  ✓ file_tasks module imported")
        
        import app.workers.maintenance_tasks
        print("  ✓ maintenance_tasks module imported")
        
        # Test that base classes are available
        assert hasattr(app.workers.audio_tasks, 'AudioProcessingTask')
        print("  ✓ AudioProcessingTask class available")
        
        assert hasattr(app.workers.analysis_tasks, 'AudioAnalysisTask')
        print("  ✓ AudioAnalysisTask class available")
        
        assert hasattr(app.workers.file_tasks, 'FileTask')
        print("  ✓ FileTask class available")
        
        assert hasattr(app.workers.maintenance_tasks, 'MaintenanceTask')
        print("  ✓ MaintenanceTask class available")
        
        print("✅ All task modules imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Task module import test failed: {e}")
        return False


def main() -> bool:
    """Run all Celery configuration tests."""
    print("🚀 Starting Celery configuration tests...\n")
    
    tests = [
        test_celery_configuration,
        test_task_registration,
        test_task_signatures,
        test_task_queues_configuration,
        test_beat_schedule,
        test_worker_configuration,
        test_import_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            break  # Stop on first failure
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Celery configuration tests completed successfully!")
        print("\nTo start Celery workers when Redis is available:")
        print("  celery -A app.core.celery_app worker --loglevel=info")
        print("  celery -A app.core.celery_app beat --loglevel=info")
        return True
    else:
        print("💥 Some tests failed. Check the Celery configuration and task definitions.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)