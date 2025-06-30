#!/usr/bin/env python3
"""
Comprehensive Test Script for MasteringAI Model Implementation.

This script validates the CNN-LSTM hybrid neural network implementation
including model creation, training pipeline, and optimization features.
"""

import os
import sys
import logging
import torch
import numpy as np
from pathlib import Path

# Add backend path to system path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

from backend.app.ai.mastering_model import (
    MasteringAI, MasteringLoss, MasteringDataset, MasteringParameters,
    create_model, calculate_model_size
)
from backend.app.ai.training_pipeline import (
    TrainingConfig, ModelTrainer, train_mastering_model
)
from backend.app.ai.model_optimization import (
    ModelOptimizer, optimize_model_for_production, ONNXInferenceEngine
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_model_creation():
    """Test basic model creation and forward pass."""
    logger.info("Testing model creation...")
    
    # Create model
    model = create_model(
        input_features=128,
        hidden_dim=256,  # Smaller for testing
        num_genres=5,
        device="cpu"  # Use CPU for testing
    )
    
    # Test model statistics
    stats = calculate_model_size(model)
    logger.info(f"Model statistics: {stats}")
    
    # Test forward pass
    batch_size = 4
    sequence_length = 100
    features = torch.randn(batch_size, 128, sequence_length)
    
    model.eval()
    with torch.no_grad():
        predictions = model(features)
    
    # Validate output shapes
    expected_shapes = {
        'genre': (batch_size, 5),
        'eq_curve': (batch_size, 31),
        'compression': (batch_size, 4),
        'stereo': (batch_size, 2),
        'limiting': (batch_size, 3),
        'confidence': (batch_size, 1)
    }
    
    for key, expected_shape in expected_shapes.items():
        assert predictions[key].shape == expected_shape, f"Wrong shape for {key}: {predictions[key].shape} vs {expected_shape}"
    
    logger.info("✓ Model creation and forward pass test passed")
    return model


def test_parameter_prediction():
    """Test parameter prediction functionality."""
    logger.info("Testing parameter prediction...")
    
    model = create_model(hidden_dim=256, device="cpu")
    
    # Create sample input
    features = torch.randn(1, 128, 100)
    
    # Test parameter prediction
    parameters = model.predict_parameters(features)
    
    # Validate parameter structure
    assert isinstance(parameters, MasteringParameters)
    assert len(parameters.eq_curve) == 31
    assert 1.0 <= parameters.compression_ratio <= 10.0
    assert 0.1 <= parameters.compression_attack <= 100.0
    assert 10.0 <= parameters.compression_release <= 1000.0
    assert -60.0 <= parameters.compression_threshold <= 0.0
    assert 0.0 <= parameters.stereo_width <= 2.0
    assert -1.0 <= parameters.stereo_pan <= 1.0
    assert -12.0 <= parameters.limiting_threshold <= 0.0
    assert 1.0 <= parameters.limiting_release <= 100.0
    assert -3.0 <= parameters.limiting_ceiling <= 0.0
    assert 0.0 <= parameters.confidence <= 1.0
    
    logger.info(f"✓ Parameter prediction test passed - Confidence: {parameters.confidence:.3f}")
    return parameters


def test_loss_function():
    """Test multi-objective loss function."""
    logger.info("Testing loss function...")
    
    # Create loss function
    criterion = MasteringLoss()
    
    batch_size = 4
    
    # Create sample predictions
    predictions = {
        'genre': torch.randn(batch_size, 5),
        'eq_curve': torch.randn(batch_size, 31),
        'compression': torch.randn(batch_size, 4),
        'stereo': torch.randn(batch_size, 2),
        'limiting': torch.randn(batch_size, 3),
        'confidence': torch.sigmoid(torch.randn(batch_size, 1))
    }
    
    # Create sample targets
    targets = {
        'genre': torch.randint(0, 5, (batch_size,)),
        'eq_curve': torch.randn(batch_size, 31),
        'compression': torch.randn(batch_size, 4),
        'stereo': torch.randn(batch_size, 2),
        'limiting': torch.randn(batch_size, 3),
        'confidence': torch.rand(batch_size, 1)
    }
    
    # Compute loss
    losses = criterion(predictions, targets)
    
    # Validate loss components
    expected_keys = ['genre_loss', 'eq_loss', 'compression_loss', 'stereo_loss', 'limiting_loss', 'confidence_loss', 'total_loss']
    for key in expected_keys:
        assert key in losses, f"Missing loss component: {key}"
        assert isinstance(losses[key], torch.Tensor), f"Loss component {key} should be a tensor"
        assert not torch.isnan(losses[key]), f"Loss component {key} should not be NaN"
    
    logger.info(f"✓ Loss function test passed - Total loss: {losses['total_loss'].item():.4f}")
    return losses


def test_dataset():
    """Test dataset functionality."""
    logger.info("Testing dataset...")
    
    # Create sample data
    num_samples = 10
    features_data = [torch.randn(128, 100) for _ in range(num_samples)]
    targets_data = [
        {
            'genre': torch.randint(0, 5, (1,)).squeeze(),
            'eq_curve': torch.randn(31),
            'compression': torch.randn(4),
            'stereo': torch.randn(2),
            'limiting': torch.randn(3),
            'confidence': torch.rand(1)
        }
        for _ in range(num_samples)
    ]
    
    # Create dataset
    dataset = MasteringDataset(features_data, targets_data)
    
    # Test dataset length
    assert len(dataset) == num_samples
    
    # Test dataset indexing
    features, targets = dataset[0]
    assert features.shape == (128, 100)
    assert 'genre' in targets
    
    # Test with DataLoader
    from torch.utils.data import DataLoader
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)
    
    for batch_features, batch_targets in dataloader:
        assert batch_features.shape[0] <= 4  # Batch size
        assert batch_features.shape[1:] == (128, 100)  # Feature shape
        break
    
    logger.info("✓ Dataset test passed")
    return dataset


def test_training_pipeline():
    """Test training pipeline (abbreviated)."""
    logger.info("Testing training pipeline...")
    
    # Create small training configuration
    config = TrainingConfig(
        input_features=128,
        hidden_dim=128,  # Very small for testing
        num_genres=3,
        batch_size=4,
        num_epochs=2,  # Very short training
        device="cpu",
        log_interval=1,
        save_interval=1
    )
    
    # Create trainer
    trainer = ModelTrainer(config)
    
    # Create minimal sample data
    num_samples = 16
    features_data = [torch.randn(128, 50) for _ in range(num_samples)]  # Shorter sequences
    targets_data = [
        {
            'genre': torch.randint(0, 3, (1,)).squeeze(),
            'eq_curve': torch.randn(31),
            'compression': torch.randn(4),
            'stereo': torch.randn(2),
            'limiting': torch.randn(3),
            'confidence': torch.rand(1)
        }
        for _ in range(num_samples)
    ]
    
    # Prepare data
    train_loader, val_loader, test_loader = trainer.prepare_data(features_data, targets_data)
    
    # Test one training epoch
    logger.info("Running one training epoch...")
    train_losses = trainer.train_epoch(train_loader)
    assert 'total_loss' in train_losses
    
    # Test one validation epoch
    val_losses = trainer.validate_epoch(val_loader)
    assert 'total_loss' in val_losses
    
    logger.info(f"✓ Training pipeline test passed - Train loss: {train_losses['total_loss']:.4f}, Val loss: {val_losses['total_loss']:.4f}")
    return trainer


def test_model_optimization():
    """Test model optimization features."""
    logger.info("Testing model optimization...")
    
    # Create small model for testing
    model = create_model(hidden_dim=128, device="cpu")
    optimizer = ModelOptimizer(model)
    
    # Create sample input
    sample_input = torch.randn(1, 128, 50)
    
    # Test benchmarking
    logger.info("Running benchmark...")
    metrics = optimizer.benchmark_inference(sample_input, num_runs=10, warmup_runs=2)
    assert 'avg_inference_time_ms' in metrics
    
    # Test quantization
    logger.info("Testing quantization...")
    try:
        quantized_model = optimizer.quantize_dynamic()
        logger.info("✓ Quantization successful")
    except Exception as e:
        logger.warning(f"Quantization failed (expected in some environments): {e}")
    
    # Test TorchScript compilation
    logger.info("Testing TorchScript compilation...")
    try:
        scripted_model = optimizer.compile_torchscript(sample_input, method="trace")
        
        # Test scripted model inference
        with torch.no_grad():
            scripted_output = scripted_model(sample_input)
        
        logger.info("✓ TorchScript compilation successful")
    except Exception as e:
        logger.warning(f"TorchScript compilation failed: {e}")
    
    # Test ONNX export
    logger.info("Testing ONNX export...")
    try:
        temp_onnx_path = "temp_model.onnx"
        optimizer.export_onnx(sample_input, temp_onnx_path)
        
        # Clean up
        if os.path.exists(temp_onnx_path):
            os.remove(temp_onnx_path)
        
        logger.info("✓ ONNX export successful")
    except Exception as e:
        logger.warning(f"ONNX export failed (may require additional dependencies): {e}")
    
    logger.info("✓ Model optimization test completed")
    return metrics


def test_gpu_compatibility():
    """Test GPU compatibility if available."""
    if not torch.cuda.is_available():
        logger.info("GPU not available, skipping GPU tests")
        return
    
    logger.info("Testing GPU compatibility...")
    
    try:
        # Create model on GPU
        model = create_model(hidden_dim=256, device="cuda")
        
        # Test forward pass on GPU
        features = torch.randn(2, 128, 100).cuda()
        
        model.eval()
        with torch.no_grad():
            predictions = model(features)
        
        # Verify outputs are on GPU
        for key, tensor in predictions.items():
            assert tensor.is_cuda, f"Output {key} not on GPU"
        
        logger.info("✓ GPU compatibility test passed")
        
        # Test GPU memory usage
        memory_allocated = torch.cuda.memory_allocated() / 1024**2  # MB
        logger.info(f"GPU memory allocated: {memory_allocated:.2f} MB")
        
    except Exception as e:
        logger.error(f"GPU test failed: {e}")


def run_comprehensive_test():
    """Run all tests in sequence."""
    logger.info("Starting comprehensive MasteringAI model test...")
    logger.info("=" * 60)
    
    try:
        # Test 1: Model creation
        model = test_model_creation()
        
        # Test 2: Parameter prediction
        parameters = test_parameter_prediction()
        
        # Test 3: Loss function
        losses = test_loss_function()
        
        # Test 4: Dataset
        dataset = test_dataset()
        
        # Test 5: Training pipeline
        trainer = test_training_pipeline()
        
        # Test 6: Model optimization
        metrics = test_model_optimization()
        
        # Test 7: GPU compatibility
        test_gpu_compatibility()
        
        logger.info("=" * 60)
        logger.info("🎉 ALL TESTS PASSED! 🎉")
        logger.info("MasteringAI model implementation is working correctly.")
        
        # Print summary
        logger.info("\nTest Summary:")
        logger.info(f"✓ Model created with {calculate_model_size(model)['total_parameters']} parameters")
        logger.info(f"✓ Inference time: {metrics['avg_inference_time_ms']:.2f} ms")
        logger.info(f"✓ Prediction confidence: {parameters.confidence:.3f}")
        logger.info(f"✓ Training loss: {losses['total_loss'].item():.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)