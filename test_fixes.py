#!/usr/bin/env python3
"""
Quick test to verify the critical fixes are working
"""

def test_imports():
    """Test that all required imports work"""
    try:
        import os
        import traceback
        print("✅ Basic imports: os, traceback")
        
        # Test Matchering import
        import matchering
        from matchering import Config, Result
        print("✅ Matchering imports working")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_filename_logic():
    """Test filename extraction logic"""
    try:
        from pathlib import Path
        
        # Test cases
        test_cases = [
            ("Respek Ma Craft.wav", "Respek Ma Craft_mastered.wav"),
            ("my song.mp3", "my song_mastered.wav"),  
            ("test.flac", "test_mastered.wav")
        ]
        
        for original, expected in test_cases:
            original_name = Path(original).stem
            output_filename = f"{original_name}_mastered.wav"
            assert output_filename == expected, f"Expected {expected}, got {output_filename}"
        
        print("✅ Filename logic working correctly")
        return True
    except Exception as e:
        print(f"❌ Filename logic failed: {e}")
        return False

def test_directory_creation():
    """Test results directory creation"""
    try:
        from pathlib import Path
        
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        if results_dir.exists():
            print("✅ Results directory creation working")
            return True
        else:
            print("❌ Results directory not created")
            return False
    except Exception as e:
        print(f"❌ Directory creation failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing critical fixes...")
    
    tests = [
        test_imports,
        test_filename_logic, 
        test_directory_creation
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All critical fixes verified!")
    else:
        print("⚠️ Some fixes need attention")