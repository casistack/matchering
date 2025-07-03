#!/usr/bin/env python3
"""
Quick test to verify our enterprise ensemble is working by checking logs.
"""

import requests
import time
import json
from pathlib import Path

def test_enterprise_ensemble():
    """Quick test of enterprise ensemble system."""
    base_url = "http://localhost:8000"
    
    # Find test audio
    test_audio = "Testuploads/Respek Ma Craft.wav"
    if not Path(test_audio).exists():
        print("❌ Test audio not found")
        return
    
    print("🧪 Testing Enterprise Ensemble with 'Respek Ma Craft.wav'")
    print("   Expected: Should classify as hip-hop/rap, not country/reggae")
    print()
    
    # Submit request (fire and forget - we'll check logs)
    try:
        with open(test_audio, 'rb') as f:
            files = {'file': ('respek_ma_craft_test.wav', f, 'audio/wav')}
            data = {
                'model_preference': 'auto',
                'processing_mode': 'hybrid',
                'intensity_level': 'medium',
                'preserve_dynamics': 'true',
                'target_loudness_lufs': '-14.0'
            }
            
            print("📤 Submitting test file...")
            response = requests.post(
                f"{base_url}/api/v1/hybrid-ai/process-hybrid",
                files=files,
                data=data,
                timeout=30  # Short timeout, we'll check logs separately
            )
            
            print(f"✅ Request submitted: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('job_id')
                print(f"🆔 Job ID: {job_id}")
            
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out (expected for background processing)")
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return
    
    print("\n🔍 Check the logs in a few seconds:")
    print("   tail -f backend/logs/processing.log | grep 'ai_prediction'")
    print("\n✅ Look for:")
    print("   - 'is_using_fallback_genre': false (AI working)")
    print("   - 'predicted_genre': 'hiphop' or 'rap' (accuracy)")
    print("   - 'model_used': 'ensemble_...' (enterprise system)")

if __name__ == "__main__":
    test_enterprise_ensemble()