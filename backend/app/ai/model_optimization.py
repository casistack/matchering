"""
Model Optimization for Production Deployment.

This module implements various optimization techniques for the MasteringAI model
including quantization, TorchScript compilation, and ONNX export for production use.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.quantization as quantization
from torch.jit import script, trace
import onnx
import onnxruntime as ort
import numpy as np

from .mastering_model import MasteringAI, MasteringParameters

logger = logging.getLogger(__name__)


class ModelOptimizer:
    """Optimization utilities for production deployment of MasteringAI models."""
    
    def __init__(self, model: MasteringAI):
        self.model = model
        self.device = next(model.parameters()).device
    
    def quantize_dynamic(
        self,
        dtype: torch.dtype = torch.qint8,
        output_path: Optional[str] = None
    ) -> nn.Module:
        """
        Apply dynamic quantization to reduce model size and improve inference speed.
        
        Args:
            dtype: Quantization data type
            output_path: Path to save quantized model
            
        Returns:
            Quantized model
        """
        logger.info("Applying dynamic quantization...")
        
        # Ensure model is in evaluation mode
        self.model.eval()
        
        # Define layers to quantize
        quantizable_layers = {nn.Linear, nn.Conv1d}
        
        # Apply dynamic quantization
        quantized_model = quantization.quantize_dynamic(
            self.model,
            quantizable_layers,
            dtype=dtype
        )
        
        # Calculate size reduction
        original_size = self._get_model_size(self.model)
        quantized_size = self._get_model_size(quantized_model)
        size_reduction = (1 - quantized_size / original_size) * 100
        
        logger.info(f"Quantization complete - Size reduction: {size_reduction:.1f}%")
        logger.info(f"Original: {original_size:.2f} MB, Quantized: {quantized_size:.2f} MB")
        
        if output_path:
            torch.save(quantized_model.state_dict(), output_path)
            logger.info(f"Saved quantized model to: {output_path}")
        
        return quantized_model
    
    def compile_torchscript(
        self,
        sample_input: torch.Tensor,
        output_path: Optional[str] = None,
        method: str = "trace"
    ) -> torch.jit.ScriptModule:
        """
        Compile model to TorchScript for optimized inference.
        
        Args:
            sample_input: Sample input tensor for tracing
            output_path: Path to save compiled model
            method: Compilation method ('trace' or 'script')
            
        Returns:
            TorchScript compiled model
        """
        logger.info(f"Compiling to TorchScript using {method} method...")
        
        self.model.eval()
        
        with torch.no_grad():
            if method == "trace":
                # Trace the model with sample input
                scripted_model = trace(self.model, sample_input)
            elif method == "script":
                # Script the model (may require model modifications for full compatibility)
                scripted_model = script(self.model)
            else:
                raise ValueError(f"Unknown compilation method: {method}")
        
        # Verify the compiled model works
        with torch.no_grad():
            original_output = self.model(sample_input)
            scripted_output = scripted_model(sample_input)
            
            # Check output consistency
            max_diff = max(
                torch.max(torch.abs(original_output[key] - scripted_output[key])).item()
                for key in original_output.keys()
            )
            
            if max_diff > 1e-5:
                logger.warning(f"Large difference detected between original and scripted model: {max_diff}")
            else:
                logger.info(f"Model compilation verified - Max difference: {max_diff:.2e}")
        
        if output_path:
            scripted_model.save(output_path)
            logger.info(f"Saved TorchScript model to: {output_path}")
        
        return scripted_model
    
    def export_onnx(
        self,
        sample_input: torch.Tensor,
        output_path: str,
        opset_version: int = 11,
        dynamic_axes: Optional[Dict[str, Dict[int, str]]] = None
    ) -> str:
        """
        Export model to ONNX format for cross-platform deployment.
        
        Args:
            sample_input: Sample input tensor
            output_path: Path to save ONNX model
            opset_version: ONNX opset version
            dynamic_axes: Dynamic axes specification
            
        Returns:
            Path to exported ONNX model
        """
        logger.info("Exporting to ONNX format...")
        
        self.model.eval()
        
        # Default dynamic axes for batch size
        if dynamic_axes is None:
            dynamic_axes = {
                'input': {0: 'batch_size'},
                'genre_output': {0: 'batch_size'},
                'eq_output': {0: 'batch_size'},
                'compression_output': {0: 'batch_size'},
                'stereo_output': {0: 'batch_size'},
                'limiting_output': {0: 'batch_size'},
                'confidence_output': {0: 'batch_size'}
            }
        
        # Create output names
        output_names = [
            'genre_output',
            'eq_output', 
            'compression_output',
            'stereo_output',
            'limiting_output',
            'confidence_output'
        ]
        
        with torch.no_grad():
            torch.onnx.export(
                self.model,
                sample_input,
                output_path,
                export_params=True,
                opset_version=opset_version,
                do_constant_folding=True,
                input_names=['input'],
                output_names=output_names,
                dynamic_axes=dynamic_axes,
                verbose=False
            )
        
        # Verify ONNX model
        try:
            onnx_model = onnx.load(output_path)
            onnx.checker.check_model(onnx_model)
            logger.info("ONNX model verification passed")
        except Exception as e:
            logger.error(f"ONNX model verification failed: {e}")
            raise
        
        logger.info(f"Exported ONNX model to: {output_path}")
        return output_path
    
    def optimize_for_mobile(
        self,
        sample_input: torch.Tensor,
        output_path: str
    ) -> str:
        """
        Optimize model for mobile deployment using PyTorch Mobile.
        
        Args:
            sample_input: Sample input tensor
            output_path: Path to save mobile-optimized model
            
        Returns:
            Path to optimized model
        """
        logger.info("Optimizing for mobile deployment...")
        
        # First compile to TorchScript
        scripted_model = self.compile_torchscript(sample_input, method="trace")
        
        # Optimize for mobile
        from torch.utils.mobile_optimizer import optimize_for_mobile
        
        mobile_model = optimize_for_mobile(scripted_model)
        mobile_model._save_for_lite_interpreter(output_path)
        
        logger.info(f"Saved mobile-optimized model to: {output_path}")
        return output_path
    
    def benchmark_inference(
        self,
        sample_input: torch.Tensor,
        num_runs: int = 100,
        warmup_runs: int = 10
    ) -> Dict[str, float]:
        """
        Benchmark model inference performance.
        
        Args:
            sample_input: Sample input for benchmarking
            num_runs: Number of benchmark runs
            warmup_runs: Number of warmup runs
            
        Returns:
            Performance metrics
        """
        logger.info(f"Benchmarking inference performance ({num_runs} runs)...")
        
        self.model.eval()
        
        # Warmup
        with torch.no_grad():
            for _ in range(warmup_runs):
                _ = self.model(sample_input)
        
        # Benchmark
        torch.cuda.synchronize() if self.device.type == 'cuda' else None
        
        start_time = time.time()
        with torch.no_grad():
            for _ in range(num_runs):
                _ = self.model(sample_input)
        
        torch.cuda.synchronize() if self.device.type == 'cuda' else None
        end_time = time.time()
        
        # Calculate metrics
        total_time = end_time - start_time
        avg_time = total_time / num_runs
        throughput = num_runs / total_time
        
        # Memory usage
        if self.device.type == 'cuda':
            memory_allocated = torch.cuda.memory_allocated(self.device) / 1024**2  # MB
            memory_reserved = torch.cuda.memory_reserved(self.device) / 1024**2  # MB
        else:
            memory_allocated = 0
            memory_reserved = 0
        
        metrics = {
            'avg_inference_time_ms': avg_time * 1000,
            'throughput_samples_per_second': throughput,
            'total_time_seconds': total_time,
            'memory_allocated_mb': memory_allocated,
            'memory_reserved_mb': memory_reserved
        }
        
        logger.info(f"Benchmark results: {metrics}")
        return metrics
    
    def compare_optimizations(
        self,
        sample_input: torch.Tensor,
        temp_dir: str = "temp_models"
    ) -> Dict[str, Dict[str, Union[float, str]]]:
        """
        Compare different optimization techniques.
        
        Args:
            sample_input: Sample input tensor
            temp_dir: Temporary directory for saved models
            
        Returns:
            Comparison results
        """
        logger.info("Comparing optimization techniques...")
        
        Path(temp_dir).mkdir(exist_ok=True)
        results = {}
        
        # Original model
        original_metrics = self.benchmark_inference(sample_input)
        original_size = self._get_model_size(self.model)
        
        results['original'] = {
            'inference_time_ms': original_metrics['avg_inference_time_ms'],
            'throughput_sps': original_metrics['throughput_samples_per_second'],
            'model_size_mb': original_size,
            'memory_mb': original_metrics['memory_allocated_mb']
        }
        
        # Dynamic quantization
        try:
            quantized_model = self.quantize_dynamic()
            
            # Create temporary optimizer for quantized model
            temp_optimizer = ModelOptimizer(quantized_model)
            quantized_metrics = temp_optimizer.benchmark_inference(sample_input)
            quantized_size = self._get_model_size(quantized_model)
            
            results['quantized'] = {
                'inference_time_ms': quantized_metrics['avg_inference_time_ms'],
                'throughput_sps': quantized_metrics['throughput_samples_per_second'],
                'model_size_mb': quantized_size,
                'memory_mb': quantized_metrics['memory_allocated_mb'],
                'speedup': original_metrics['avg_inference_time_ms'] / quantized_metrics['avg_inference_time_ms'],
                'size_reduction': (1 - quantized_size / original_size) * 100
            }
        except Exception as e:
            logger.error(f"Quantization benchmark failed: {e}")
            results['quantized'] = {'error': str(e)}
        
        # TorchScript
        try:
            scripted_model = self.compile_torchscript(sample_input)
            
            # Benchmark TorchScript model
            torch.cuda.synchronize() if self.device.type == 'cuda' else None
            start_time = time.time()
            
            with torch.no_grad():
                for _ in range(100):
                    _ = scripted_model(sample_input)
            
            torch.cuda.synchronize() if self.device.type == 'cuda' else None
            end_time = time.time()
            
            scripted_time = (end_time - start_time) / 100 * 1000  # ms
            scripted_size = self._get_torchscript_size(scripted_model)
            
            results['torchscript'] = {
                'inference_time_ms': scripted_time,
                'throughput_sps': 1000 / scripted_time,
                'model_size_mb': scripted_size,
                'speedup': original_metrics['avg_inference_time_ms'] / scripted_time
            }
        except Exception as e:
            logger.error(f"TorchScript benchmark failed: {e}")
            results['torchscript'] = {'error': str(e)}
        
        # ONNX
        try:
            onnx_path = f"{temp_dir}/model.onnx"
            self.export_onnx(sample_input, onnx_path)
            
            # Benchmark ONNX model
            ort_session = ort.InferenceSession(onnx_path)
            input_name = ort_session.get_inputs()[0].name
            
            # Convert to numpy for ONNX
            np_input = sample_input.cpu().numpy()
            
            start_time = time.time()
            for _ in range(100):
                _ = ort_session.run(None, {input_name: np_input})
            end_time = time.time()
            
            onnx_time = (end_time - start_time) / 100 * 1000  # ms
            onnx_size = Path(onnx_path).stat().st_size / 1024**2  # MB
            
            results['onnx'] = {
                'inference_time_ms': onnx_time,
                'throughput_sps': 1000 / onnx_time,
                'model_size_mb': onnx_size,
                'speedup': original_metrics['avg_inference_time_ms'] / onnx_time
            }
        except Exception as e:
            logger.error(f"ONNX benchmark failed: {e}")
            results['onnx'] = {'error': str(e)}
        
        logger.info("Optimization comparison complete")
        return results
    
    def _get_model_size(self, model: nn.Module) -> float:
        """Get model size in MB."""
        param_size = 0
        buffer_size = 0
        
        for param in model.parameters():
            param_size += param.nelement() * param.element_size()
        
        for buffer in model.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()
        
        size_mb = (param_size + buffer_size) / 1024**2
        return size_mb
    
    def _get_torchscript_size(self, model: torch.jit.ScriptModule) -> float:
        """Get TorchScript model size in MB (approximation)."""
        # This is an approximation - actual size would require saving to disk
        return self._get_model_size(model)


class ONNXInferenceEngine:
    """Optimized ONNX inference engine for production deployment."""
    
    def __init__(self, onnx_model_path: str, providers: Optional[List[str]] = None):
        self.model_path = onnx_model_path
        
        # Default providers (GPU if available, then CPU)
        if providers is None:
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        
        # Create inference session
        self.session = ort.InferenceSession(onnx_model_path, providers=providers)
        
        # Get input/output info
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [output.name for output in self.session.get_outputs()]
        
        logger.info(f"Initialized ONNX inference engine with providers: {self.session.get_providers()}")
    
    def predict(self, features: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Run inference on audio features.
        
        Args:
            features: Input features as numpy array
            
        Returns:
            Prediction results
        """
        # Run inference
        outputs = self.session.run(self.output_names, {self.input_name: features})
        
        # Map outputs to names
        results = dict(zip(self.output_names, outputs))
        
        return results
    
    def predict_parameters(self, features: np.ndarray) -> MasteringParameters:
        """
        Predict mastering parameters from features.
        
        Args:
            features: Input features
            
        Returns:
            Structured mastering parameters
        """
        predictions = self.predict(features)
        
        # Process predictions similar to PyTorch model
        # This would need to be implemented based on the specific output format
        # For now, return a placeholder
        
        # TODO: Implement proper parameter conversion from ONNX outputs
        return MasteringParameters(
            genre_probabilities={"placeholder": 1.0},
            predicted_genre="placeholder",
            eq_curve=[0.0] * 31,
            compression_ratio=2.0,
            compression_attack=10.0,
            compression_release=100.0,
            compression_threshold=-20.0,
            stereo_width=1.0,
            stereo_pan=0.0,
            limiting_threshold=-1.0,
            limiting_release=50.0,
            limiting_ceiling=-0.1,
            confidence=0.8
        )


def optimize_model_for_production(
    model: MasteringAI,
    sample_input: torch.Tensor,
    output_dir: str = "optimized_models",
    formats: List[str] = ["quantized", "torchscript", "onnx"]
) -> Dict[str, str]:
    """
    Optimize model for production deployment in multiple formats.
    
    Args:
        model: Trained MasteringAI model
        sample_input: Sample input tensor
        output_dir: Directory to save optimized models
        formats: List of optimization formats to generate
        
    Returns:
        Dictionary mapping format names to file paths
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    optimizer = ModelOptimizer(model)
    output_paths = {}
    
    if "quantized" in formats:
        quantized_path = Path(output_dir) / "model_quantized.pth"
        optimizer.quantize_dynamic(output_path=str(quantized_path))
        output_paths["quantized"] = str(quantized_path)
    
    if "torchscript" in formats:
        torchscript_path = Path(output_dir) / "model_scripted.pt"
        optimizer.compile_torchscript(sample_input, output_path=str(torchscript_path))
        output_paths["torchscript"] = str(torchscript_path)
    
    if "onnx" in formats:
        onnx_path = Path(output_dir) / "model.onnx"
        optimizer.export_onnx(sample_input, str(onnx_path))
        output_paths["onnx"] = str(onnx_path)
    
    if "mobile" in formats:
        mobile_path = Path(output_dir) / "model_mobile.ptl"
        optimizer.optimize_for_mobile(sample_input, str(mobile_path))
        output_paths["mobile"] = str(mobile_path)
    
    # Generate performance comparison report
    comparison_results = optimizer.compare_optimizations(sample_input)
    
    # Save comparison report
    import json
    report_path = Path(output_dir) / "optimization_report.json"
    with open(report_path, 'w') as f:
        json.dump(comparison_results, f, indent=2)
    
    logger.info(f"Model optimization complete. Files saved to: {output_dir}")
    return output_paths