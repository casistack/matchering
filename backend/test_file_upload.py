#!/usr/bin/env python3
"""
File Upload API testing script for Enhanced Matchering API.

This script tests the complete file upload workflow including validation,
processing, and error handling without requiring a running server.
"""

import asyncio
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any
import logging

# Add the app directory to path for imports
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal, engine, Base
from app.models.audio import AudioFile, AudioMetadata
from app.utils.file_utils import (
    save_uploaded_file,
    validate_audio_file,
    calculate_file_checksum,
    generate_unique_filename,
    sanitize_filename,
    extract_basic_audio_properties
)
from app.utils.validation_utils import (
    validate_file_format,
    validate_file_size,
    validate_processing_mode,
    validate_pagination_params
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class MockUploadFile:
    """Mock UploadFile for testing purposes."""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "audio/wav"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self._position = 0
    
    async def read(self, size: int = -1) -> bytes:
        """Read file content."""
        if size == -1:
            chunk = self.content[self._position:]
            self._position = len(self.content)
        else:
            chunk = self.content[self._position:self._position + size]
            self._position += len(chunk)
        return chunk
    
    async def seek(self, position: int) -> int:
        """Seek to position in file."""
        self._position = max(0, min(position, len(self.content)))
        return self._position


def create_test_audio_content(size_bytes: int = 1024) -> bytes:
    """Create test audio file content."""
    # Create simple audio-like content (not actual audio)
    header = b"RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
    data = b"\x00" * (size_bytes - len(header))
    return header + data


async def test_file_utilities() -> bool:
    """Test file utility functions."""
    print("🔧 Testing file utilities...")
    
    try:
        # Test filename sanitization
        test_filenames = [
            ("normal_file.wav", "normal_file.wav"),
            ("file with spaces.mp3", "file with spaces.mp3"),
            ("file/with\\dangerous:chars.flac", "file_with_dangerous_chars.flac"),
            ("", "file_"),  # Will get unique ID added
            ("..\\..\\hack.wav", "____hack.wav"),
        ]
        
        for input_name, expected_pattern in test_filenames:
            result = sanitize_filename(input_name)
            if expected_pattern.endswith("_") and result.startswith("upload_"):
                print(f"  ✓ Sanitized '{input_name}' -> '{result}' (generated)")
            elif expected_pattern in result or input_name == result:
                print(f"  ✓ Sanitized '{input_name}' -> '{result}'")
            else:
                print(f"  ❌ Unexpected sanitization: '{input_name}' -> '{result}'")
                return False
        
        # Test unique filename generation
        unique1 = generate_unique_filename("test.wav")
        unique2 = generate_unique_filename("test.wav")
        
        if unique1 != unique2 and unique1.endswith(".wav") and unique2.endswith(".wav"):
            print(f"  ✓ Unique filename generation working")
        else:
            print(f"  ❌ Unique filename generation failed")
            return False
        
        # Test basic audio properties extraction
        test_path = Path("test.wav")
        properties = await extract_basic_audio_properties(test_path)
        
        if "sample_rate" in properties and "channels" in properties:
            print(f"  ✓ Audio properties extraction working")
        else:
            print(f"  ❌ Audio properties extraction failed")
            return False
        
        print("✅ File utilities test passed")
        return True
        
    except Exception as e:
        print(f"❌ File utilities test failed: {e}")
        return False


async def test_validation_utilities() -> bool:
    """Test validation utility functions."""
    print("\n📋 Testing validation utilities...")
    
    try:
        # Test file format validation
        valid_formats = ["test.wav", "audio.mp3", "song.flac", "track.aiff"]
        for filename in valid_formats:
            try:
                validate_file_format(filename)
                print(f"  ✓ Valid format: {filename}")
            except Exception as e:
                print(f"  ❌ Should be valid: {filename} - {e}")
                return False
        
        # Test invalid formats
        invalid_formats = ["test.txt", "audio.exe", "song.pdf"]
        for filename in invalid_formats:
            try:
                validate_file_format(filename)
                print(f"  ❌ Should be invalid: {filename}")
                return False
            except Exception:
                print(f"  ✓ Correctly rejected: {filename}")
        
        # Test file size validation
        try:
            validate_file_size(1000)  # Valid size
            print(f"  ✓ Valid file size accepted")
        except Exception:
            print(f"  ❌ Valid file size rejected")
            return False
        
        try:
            validate_file_size(settings.MAX_FILE_SIZE + 1)  # Too large
            print(f"  ❌ Large file size should be rejected")
            return False
        except Exception:
            print(f"  ✓ Large file size correctly rejected")
        
        # Test processing mode validation
        valid_modes = ["auto", "reference", "hybrid"]
        for mode in valid_modes:
            try:
                validate_processing_mode(mode)
                print(f"  ✓ Valid mode: {mode}")
            except Exception:
                print(f"  ❌ Should be valid mode: {mode}")
                return False
        
        try:
            validate_processing_mode("invalid_mode")
            print(f"  ❌ Invalid mode should be rejected")
            return False
        except Exception:
            print(f"  ✓ Invalid mode correctly rejected")
        
        # Test pagination validation
        try:
            validate_pagination_params(0, 100)  # Valid
            validate_pagination_params(10, 50)  # Valid
            print(f"  ✓ Valid pagination parameters accepted")
        except Exception:
            print(f"  ❌ Valid pagination parameters rejected")
            return False
        
        try:
            validate_pagination_params(-1, 100)  # Invalid skip
            print(f"  ❌ Invalid skip should be rejected")
            return False
        except Exception:
            print(f"  ✓ Invalid skip correctly rejected")
        
        print("✅ Validation utilities test passed")
        return True
        
    except Exception as e:
        print(f"❌ Validation utilities test failed: {e}")
        return False


async def test_file_upload_workflow() -> bool:
    """Test complete file upload workflow."""
    print("\n📤 Testing file upload workflow...")
    
    try:
        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Override upload directory for test
            original_upload_dir = settings.UPLOAD_DIR
            settings.UPLOAD_DIR = temp_path
            
            try:
                # Create test file
                test_content = create_test_audio_content(2048)
                mock_file = MockUploadFile("test_upload.wav", test_content)
                
                # Test file saving
                saved_path, checksum = await save_uploaded_file(mock_file, temp_path)
                
                if saved_path.exists() and len(checksum) == 64:
                    print(f"  ✓ File saved successfully: {saved_path.name}")
                    print(f"  ✓ Checksum calculated: {checksum[:8]}...")
                else:
                    print(f"  ❌ File saving failed")
                    return False
                
                # Test file validation
                validation_result = await validate_audio_file(saved_path, mock_file)
                
                if "file_size" in validation_result and "format" in validation_result:
                    print(f"  ✓ File validation successful")
                    print(f"    - Size: {validation_result['file_size']} bytes")
                    print(f"    - Format: {validation_result['format']}")
                    print(f"    - MIME: {validation_result['mime_type']}")
                else:
                    print(f"  ❌ File validation failed")
                    return False
                
                # Test checksum calculation
                calculated_checksum = await calculate_file_checksum(saved_path)
                
                if calculated_checksum == checksum:
                    print(f"  ✓ Checksum verification successful")
                else:
                    print(f"  ❌ Checksum mismatch")
                    return False
                
                # Test duplicate detection scenario
                mock_file2 = MockUploadFile("duplicate.wav", test_content)
                saved_path2, checksum2 = await save_uploaded_file(mock_file2, temp_path)
                
                if checksum == checksum2:
                    print(f"  ✓ Duplicate detection would work (same checksum)")
                else:
                    print(f"  ❌ Duplicate detection issue")
                    return False
                
                # Clean up test files
                saved_path.unlink()
                saved_path2.unlink()
                
            finally:
                # Restore original upload directory
                settings.UPLOAD_DIR = original_upload_dir
        
        print("✅ File upload workflow test passed")
        return True
        
    except Exception as e:
        print(f"❌ File upload workflow test failed: {e}")
        return False


async def test_database_integration() -> bool:
    """Test database integration for file uploads."""
    print("\n💾 Testing database integration...")
    
    try:
        # Create database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with AsyncSessionLocal() as session:
            # Create test audio file record
            test_id = uuid.uuid4()
            audio_file = AudioFile(
                id=test_id,
                filename="test_db.wav",
                original_filename="original_test.wav",
                file_path="/uploads/test_db.wav",
                file_size=2048,
                mime_type="audio/wav",
                checksum="test_checksum_for_db_test",
                format="wav",
                sample_rate=44100,
                bit_depth=16,
                channels=2,
                duration=120.0,
                processing_eligible=True
            )
            
            session.add(audio_file)
            await session.commit()
            await session.refresh(audio_file)
            
            print(f"  ✓ Audio file record created: {audio_file.id}")
            
            # Create test metadata record
            metadata = AudioMetadata(
                id=uuid.uuid4(),
                audio_file_id=test_id,
                rms_level=-12.5,
                peak_level=-3.2,
                lufs_integrated=-14.0,
                mfcc_features={"test": "data"},
                analysis_version="1.0.0"
            )
            
            session.add(metadata)
            await session.commit()
            await session.refresh(metadata)
            
            print(f"  ✓ Metadata record created: {metadata.id}")
            
            # Test file querying
            from sqlalchemy import select
            
            query = select(AudioFile).where(AudioFile.checksum == "test_checksum_for_db_test")
            result = await session.execute(query)
            retrieved_file = result.scalar_one_or_none()
            
            if retrieved_file and retrieved_file.id == test_id:
                print(f"  ✓ File record retrieved successfully")
            else:
                print(f"  ❌ File record retrieval failed")
                return False
            
            # Test metadata querying
            metadata_query = select(AudioMetadata).where(AudioMetadata.audio_file_id == test_id)
            metadata_result = await session.execute(metadata_query)
            retrieved_metadata = metadata_result.scalar_one_or_none()
            
            if retrieved_metadata and retrieved_metadata.rms_level == -12.5:
                print(f"  ✓ Metadata record retrieved successfully")
            else:
                print(f"  ❌ Metadata record retrieval failed")
                return False
            
            # Test duplicate detection query
            duplicate_query = select(AudioFile).where(AudioFile.checksum == "test_checksum_for_db_test")
            duplicate_result = await session.execute(duplicate_query)
            duplicate_file = duplicate_result.scalar_one_or_none()
            
            if duplicate_file:
                print(f"  ✓ Duplicate detection query works")
            else:
                print(f"  ❌ Duplicate detection query failed")
                return False
            
            # Cleanup test data
            await session.delete(metadata)
            await session.delete(audio_file)
            await session.commit()
            
            print(f"  ✓ Test data cleaned up")
        
        print("✅ Database integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False


async def test_error_handling() -> bool:
    """Test error handling scenarios."""
    print("\n🚨 Testing error handling...")
    
    try:
        # Test file not found error
        try:
            non_existent_path = Path("/non/existent/file.wav")
            await validate_audio_file(non_existent_path, MockUploadFile("test.wav", b""))
            print(f"  ❌ Should have failed for non-existent file")
            return False
        except Exception:
            print(f"  ✓ Correctly handled non-existent file")
        
        # Test empty file error
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        # File exists but is empty
        try:
            await validate_audio_file(tmp_path, MockUploadFile("empty.wav", b""))
            print(f"  ❌ Should have failed for empty file")
            return False
        except Exception:
            print(f"  ✓ Correctly handled empty file")
        finally:
            tmp_path.unlink()
        
        # Test invalid format error
        try:
            validate_file_format("document.pdf")
            print(f"  ❌ Should have failed for invalid format")
            return False
        except Exception:
            print(f"  ✓ Correctly handled invalid format")
        
        # Test file too large error
        try:
            validate_file_size(settings.MAX_FILE_SIZE + 1000)
            print(f"  ❌ Should have failed for large file")
            return False
        except Exception:
            print(f"  ✓ Correctly handled large file")
        
        # Test invalid processing mode
        try:
            validate_processing_mode("invalid")
            print(f"  ❌ Should have failed for invalid mode")
            return False
        except Exception:
            print(f"  ✓ Correctly handled invalid processing mode")
        
        print("✅ Error handling test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def test_performance_scenarios() -> bool:
    """Test performance-related scenarios."""
    print("\n⚡ Testing performance scenarios...")
    
    try:
        # Test large file handling (simulate)
        large_content = create_test_audio_content(10 * 1024 * 1024)  # 10MB
        
        if len(large_content) == 10 * 1024 * 1024:
            print(f"  ✓ Large file content creation: {len(large_content)} bytes")
        else:
            print(f"  ❌ Large file content creation failed")
            return False
        
        # Test checksum calculation performance
        import time
        start_time = time.time()
        
        import hashlib
        hash_obj = hashlib.sha256()
        hash_obj.update(large_content)
        checksum = hash_obj.hexdigest()
        
        calc_time = time.time() - start_time
        
        if len(checksum) == 64 and calc_time < 1.0:  # Should be fast
            print(f"  ✓ Checksum calculation: {calc_time:.3f}s for 10MB")
        else:
            print(f"  ⚠️ Checksum calculation slow: {calc_time:.3f}s")
        
        # Test multiple file handling
        test_files = []
        for i in range(5):
            content = create_test_audio_content(1024 * (i + 1))
            mock_file = MockUploadFile(f"test_{i}.wav", content)
            test_files.append(mock_file)
        
        if len(test_files) == 5:
            print(f"  ✓ Multiple file handling preparation")
        else:
            print(f"  ❌ Multiple file handling failed")
            return False
        
        # Test concurrent checksum calculation
        import asyncio
        
        async def calc_checksum(content):
            hash_obj = hashlib.sha256()
            hash_obj.update(content)
            return hash_obj.hexdigest()
        
        start_time = time.time()
        tasks = [calc_checksum(tf.content) for tf in test_files]
        checksums = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time
        
        if len(checksums) == 5 and all(len(cs) == 64 for cs in checksums):
            print(f"  ✓ Concurrent checksum calculation: {concurrent_time:.3f}s")
        else:
            print(f"  ❌ Concurrent checksum calculation failed")
            return False
        
        print("✅ Performance scenarios test passed")
        return True
        
    except Exception as e:
        print(f"❌ Performance scenarios test failed: {e}")
        return False


async def main() -> bool:
    """Run all file upload tests."""
    print("🚀 Starting File Upload API tests...\n")
    
    tests = [
        test_file_utilities,
        test_validation_utilities,
        test_file_upload_workflow,
        test_database_integration,
        test_error_handling,
        test_performance_scenarios
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
        print("🎉 All file upload tests completed successfully!")
        return True
    else:
        print("💥 Some tests failed. Check the file upload implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)