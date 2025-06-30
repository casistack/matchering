#!/usr/bin/env python3
"""
Test script to validate Enhanced Matchering GPU setup.
Run with: uv run python run_with_cuda.py test_gpu_setup.py
"""

import torch
import torchaudio
import numpy as np
import transformers
import time

def test_gpu_acceleration():
    """Test GPU-accelerated audio processing pipeline."""
    
    print("🚀 Enhanced Matchering GPU Setup Test")
    print("=" * 50)
    
    # Environment check
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"✅ TorchAudio: {torchaudio.__version__}")
    print(f"✅ Transformers: {transformers.__version__}")
    print(f"✅ CUDA Available: {torch.cuda.is_available()}")
    
    if not torch.cuda.is_available():
        print("❌ CUDA not available - exiting")
        return False
    
    # GPU information
    device = torch.device('cuda')
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory // 1024**3
    
    print(f"🎯 GPU: {gpu_name}")
    print(f"💾 GPU Memory: {gpu_memory} GB")
    
    print("\n📊 GPU Audio Processing Test")
    print("-" * 30)
    
    # Test 1: GPU-accelerated waveform processing
    print("🎵 Test 1: GPU Waveform Processing...")
    
    # Create test audio (2 channels, 5 seconds at 22050 Hz)
    sample_rate = 22050
    duration = 5
    waveform_cpu = torch.randn(2, sample_rate * duration)
    waveform_gpu = waveform_cpu.to(device)
    
    print(f"   Input shape: {waveform_gpu.shape} on {waveform_gpu.device}")
    
    # Test 2: GPU-accelerated transforms
    print("🔊 Test 2: GPU Audio Transforms...")
    
    transforms = {
        'MelSpectrogram': torchaudio.transforms.MelSpectrogram(
            sample_rate=sample_rate, 
            n_mels=128
        ).to(device),
        'MFCC': torchaudio.transforms.MFCC(
            sample_rate=sample_rate, 
            n_mfcc=13
        ).to(device),
        'Spectrogram': torchaudio.transforms.Spectrogram().to(device)
    }
    
    results = {}
    for name, transform in transforms.items():
        start_time = time.time()
        result = transform(waveform_gpu)
        end_time = time.time()
        
        results[name] = {
            'shape': result.shape,
            'device': result.device,
            'time': end_time - start_time
        }
        
        print(f"   ✅ {name}: {result.shape} ({end_time - start_time:.4f}s)")
    
    # Test 3: Batch processing simulation
    print("📦 Test 3: Batch Processing Simulation...")
    
    batch_size = 8  # Simulate processing 8 audio files at once
    batch_waveform = torch.randn(batch_size, 2, sample_rate * 2).to(device)  # 2-second clips
    
    mel_transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=sample_rate, 
        n_mels=64
    ).to(device)
    
    start_time = time.time()
    # Process each item in the batch
    batch_results = []
    for i in range(batch_size):
        result = mel_transform(batch_waveform[i])
        batch_results.append(result)
    batch_result = torch.stack(batch_results)
    end_time = time.time()
    
    print(f"   ✅ Batch processing: {batch_result.shape} ({end_time - start_time:.4f}s)")
    print(f"   📈 Throughput: {batch_size / (end_time - start_time):.2f} files/second")
    
    # Memory usage check
    memory_allocated = torch.cuda.memory_allocated(device) / 1024**2  # MB
    memory_reserved = torch.cuda.memory_reserved(device) / 1024**2   # MB
    
    print(f"\n💾 GPU Memory Usage:")
    print(f"   Allocated: {memory_allocated:.1f} MB")
    print(f"   Reserved: {memory_reserved:.1f} MB")
    
    print("\n🎉 All tests passed! Enhanced Matchering GPU setup is ready.")
    print("\n📚 Ready for M4-2a: CNN-LSTM neural network implementation")
    
    return True

if __name__ == "__main__":
    test_gpu_acceleration()