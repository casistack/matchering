"""
AI Mastering Model Implementation.

This module implements the CNN-LSTM hybrid neural network for audio mastering
parameter prediction as specified in the AI integration architecture.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MasteringParameters(BaseModel):
    """Structured mastering parameters predicted by AI model."""
    
    # Genre Classification
    genre_probabilities: Dict[str, float] = Field(description="Genre classification probabilities")
    predicted_genre: str = Field(description="Most likely genre")
    
    # EQ Parameters (31-band EQ curve)
    eq_curve: List[float] = Field(description="31-band EQ gains in dB (-12 to +12)")
    
    # Compression Parameters
    compression_ratio: float = Field(description="Compression ratio (1.0 to 10.0)")
    compression_attack: float = Field(description="Attack time in ms (0.1 to 100)")
    compression_release: float = Field(description="Release time in ms (10 to 1000)")
    compression_threshold: float = Field(description="Threshold in dB (-60 to 0)")
    
    # Stereo Processing
    stereo_width: float = Field(description="Stereo width factor (0.0 to 2.0)")
    stereo_pan: float = Field(description="Stereo pan (-1.0 to 1.0)")
    
    # Limiting Parameters
    limiting_threshold: float = Field(description="Limiter threshold in dB (-12 to 0)")
    limiting_release: float = Field(description="Limiter release time in ms (1 to 100)")
    limiting_ceiling: float = Field(description="Output ceiling in dB (-3 to 0)")
    
    # Confidence Score
    confidence: float = Field(description="Model confidence score (0.0 to 1.0)")


class MasteringAI(nn.Module):
    """
    CNN-LSTM hybrid neural network for audio mastering parameter prediction.
    
    Architecture:
    1. CNN layers for spectral feature processing
    2. LSTM layers for temporal modeling
    3. Multi-task heads for different parameter types
    
    Based on the architecture specification in docs/architecture/ai-integration-architecture.md
    """
    
    def __init__(
        self,
        input_features: int = 128,  # Based on feature extraction output
        hidden_dim: int = 512,
        num_genres: int = 10,
        dropout_rate: float = 0.3,
        num_cnn_layers: int = 3,
        num_lstm_layers: int = 2
    ):
        super(MasteringAI, self).__init__()
        
        self.input_features = input_features
        self.hidden_dim = hidden_dim
        self.num_genres = num_genres
        
        # CNN Feature Processing Layers
        self.feature_cnn = self._build_cnn_layers(input_features, hidden_dim, num_cnn_layers, dropout_rate)
        
        # Calculate CNN output size for LSTM input
        cnn_output_dim = 256  # Final CNN layer output
        
        # Bidirectional LSTM for temporal modeling
        self.lstm = nn.LSTM(
            input_size=cnn_output_dim,
            hidden_size=hidden_dim // 2,  # Bidirectional doubles the output
            num_layers=num_lstm_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout_rate if num_lstm_layers > 1 else 0
        )
        
        # Attention mechanism for better temporal aggregation
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=8,
            dropout=dropout_rate,
            batch_first=True
        )
        
        # Multi-task prediction heads
        self.genre_classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim // 2, num_genres)
        )
        
        # EQ predictor (31-band EQ)
        self.eq_predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim // 2, 31)
        )
        
        # Compression parameters predictor
        self.compression_predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim // 4, 4)  # ratio, attack, release, threshold
        )
        
        # Stereo processing predictor
        self.stereo_predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim // 4, 2)  # width, pan
        )
        
        # Limiting parameters predictor
        self.limiting_predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim // 4, 3)  # threshold, release, ceiling
        )
        
        # Confidence estimator
        self.confidence_estimator = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim // 4, 1),
            nn.Sigmoid()
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _build_cnn_layers(
        self,
        input_features: int,
        hidden_dim: int,
        num_layers: int,
        dropout_rate: float
    ) -> nn.Module:
        """Build CNN layers for feature processing."""
        
        layers = []
        in_channels = input_features
        
        # Progressive channel expansion
        channel_sizes = [64, 128, 256]
        
        for i in range(num_layers):
            out_channels = channel_sizes[i] if i < len(channel_sizes) else 256
            
            layers.extend([
                nn.Conv1d(in_channels, out_channels, kernel_size=3, padding=1),
                nn.BatchNorm1d(out_channels),
                nn.ReLU(inplace=True),
                nn.MaxPool1d(kernel_size=2, stride=2),
                nn.Dropout(dropout_rate)
            ])
            
            in_channels = out_channels
        
        # Global average pooling to reduce sequence length
        layers.append(nn.AdaptiveAvgPool1d(1))
        
        return nn.Sequential(*layers)
    
    def _initialize_weights(self):
        """Initialize model weights using Xavier/He initialization."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Conv1d):
                nn.init.kaiming_normal_(module.weight, mode='fan_out', nonlinearity='relu')
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)
            elif isinstance(module, nn.LSTM):
                for name, param in module.named_parameters():
                    if 'weight' in name:
                        nn.init.xavier_uniform_(param)
                    elif 'bias' in name:
                        nn.init.zeros_(param)
    
    def forward(self, features: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass through the network.
        
        Args:
            features: Input features tensor of shape (batch_size, features, time_steps)
        
        Returns:
            Dictionary containing predictions for all tasks
        """
        batch_size = features.size(0)
        
        # CNN feature extraction
        # Input: (batch_size, features, time_steps)
        cnn_out = self.feature_cnn(features)  # (batch_size, 256, 1)
        cnn_out = cnn_out.squeeze(-1)  # (batch_size, 256)
        
        # Prepare for LSTM (add sequence dimension)
        lstm_input = cnn_out.unsqueeze(1)  # (batch_size, 1, 256)
        
        # LSTM temporal modeling
        lstm_out, (hidden, cell) = self.lstm(lstm_input)  # (batch_size, 1, hidden_dim)
        
        # Apply attention mechanism for better feature aggregation
        attended_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Global pooling across sequence dimension
        pooled_features = attended_out.mean(dim=1)  # (batch_size, hidden_dim)
        
        # Multi-task predictions
        predictions = {
            'genre': self.genre_classifier(pooled_features),
            'eq_curve': self.eq_predictor(pooled_features),
            'compression': self.compression_predictor(pooled_features),
            'stereo': self.stereo_predictor(pooled_features),
            'limiting': self.limiting_predictor(pooled_features),
            'confidence': self.confidence_estimator(pooled_features)
        }
        
        return predictions
    
    def predict_parameters(self, features: torch.Tensor) -> MasteringParameters:
        """
        Predict mastering parameters from audio features.
        
        Args:
            features: Audio features tensor
            
        Returns:
            Structured mastering parameters
        """
        self.eval()
        
        with torch.no_grad():
            predictions = self.forward(features)
            
            # Process genre predictions
            genre_probs = F.softmax(predictions['genre'], dim=-1)
            genre_names = [f"genre_{i}" for i in range(self.num_genres)]  # TODO: Add real genre names
            genre_dict = {name: float(prob) for name, prob in zip(genre_names, genre_probs[0])}
            predicted_genre = max(genre_dict, key=genre_dict.get)
            
            # Process EQ curve (map to dB range -12 to +12)
            eq_curve = torch.tanh(predictions['eq_curve'][0]) * 12.0
            
            # Process compression parameters
            comp_params = torch.sigmoid(predictions['compression'][0])
            compression_ratio = comp_params[0] * 9.0 + 1.0  # 1.0 to 10.0
            compression_attack = comp_params[1] * 99.9 + 0.1  # 0.1 to 100 ms
            compression_release = comp_params[2] * 990.0 + 10.0  # 10 to 1000 ms
            compression_threshold = comp_params[3] * 60.0 - 60.0  # -60 to 0 dB
            
            # Process stereo parameters
            stereo_params = torch.tanh(predictions['stereo'][0])
            stereo_width = (stereo_params[0] + 1.0) * 1.0  # 0.0 to 2.0
            stereo_pan = stereo_params[1]  # -1.0 to 1.0
            
            # Process limiting parameters
            limiting_params = torch.sigmoid(predictions['limiting'][0])
            limiting_threshold = limiting_params[0] * 12.0 - 12.0  # -12 to 0 dB
            limiting_release = limiting_params[1] * 99.0 + 1.0  # 1 to 100 ms
            limiting_ceiling = limiting_params[2] * 3.0 - 3.0  # -3 to 0 dB
            
            # Confidence score
            confidence = float(predictions['confidence'][0])
            
            return MasteringParameters(
                genre_probabilities=genre_dict,
                predicted_genre=predicted_genre,
                eq_curve=eq_curve.tolist(),
                compression_ratio=float(compression_ratio),
                compression_attack=float(compression_attack),
                compression_release=float(compression_release),
                compression_threshold=float(compression_threshold),
                stereo_width=float(stereo_width),
                stereo_pan=float(stereo_pan),
                limiting_threshold=float(limiting_threshold),
                limiting_release=float(limiting_release),
                limiting_ceiling=float(limiting_ceiling),
                confidence=confidence
            )


class MasteringLoss(nn.Module):
    """
    Multi-objective loss function for mastering AI training.
    
    Combines:
    - Genre classification loss (Cross-entropy)
    - Parameter prediction losses (MSE)
    - Confidence-aware weighting
    """
    
    def __init__(
        self,
        genre_weight: float = 0.2,
        eq_weight: float = 0.3,
        compression_weight: float = 0.2,
        stereo_weight: float = 0.1,
        limiting_weight: float = 0.1,
        confidence_weight: float = 0.1
    ):
        super(MasteringLoss, self).__init__()
        
        self.genre_weight = genre_weight
        self.eq_weight = eq_weight
        self.compression_weight = compression_weight
        self.stereo_weight = stereo_weight
        self.limiting_weight = limiting_weight
        self.confidence_weight = confidence_weight
        
        # Loss functions
        self.cross_entropy = nn.CrossEntropyLoss()
        self.mse = nn.MSELoss()
        self.bce = nn.BCELoss()
    
    def forward(
        self,
        predictions: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Compute multi-objective loss.
        
        Args:
            predictions: Model predictions
            targets: Ground truth targets
            
        Returns:
            Dictionary of loss components and total loss
        """
        losses = {}
        
        # Genre classification loss
        if 'genre' in targets:
            losses['genre_loss'] = self.cross_entropy(predictions['genre'], targets['genre'])
        else:
            losses['genre_loss'] = torch.tensor(0.0, device=predictions['genre'].device)
        
        # EQ curve loss
        if 'eq_curve' in targets:
            losses['eq_loss'] = self.mse(predictions['eq_curve'], targets['eq_curve'])
        else:
            losses['eq_loss'] = torch.tensor(0.0, device=predictions['eq_curve'].device)
        
        # Compression parameters loss
        if 'compression' in targets:
            losses['compression_loss'] = self.mse(predictions['compression'], targets['compression'])
        else:
            losses['compression_loss'] = torch.tensor(0.0, device=predictions['compression'].device)
        
        # Stereo parameters loss
        if 'stereo' in targets:
            losses['stereo_loss'] = self.mse(predictions['stereo'], targets['stereo'])
        else:
            losses['stereo_loss'] = torch.tensor(0.0, device=predictions['stereo'].device)
        
        # Limiting parameters loss
        if 'limiting' in targets:
            losses['limiting_loss'] = self.mse(predictions['limiting'], targets['limiting'])
        else:
            losses['limiting_loss'] = torch.tensor(0.0, device=predictions['limiting'].device)
        
        # Confidence loss (if available)
        if 'confidence' in targets:
            losses['confidence_loss'] = self.bce(predictions['confidence'], targets['confidence'])
        else:
            losses['confidence_loss'] = torch.tensor(0.0, device=predictions['confidence'].device)
        
        # Total weighted loss
        total_loss = (
            self.genre_weight * losses['genre_loss'] +
            self.eq_weight * losses['eq_loss'] +
            self.compression_weight * losses['compression_loss'] +
            self.stereo_weight * losses['stereo_loss'] +
            self.limiting_weight * losses['limiting_loss'] +
            self.confidence_weight * losses['confidence_loss']
        )
        
        losses['total_loss'] = total_loss
        
        return losses


class MasteringDataset(Dataset):
    """
    Dataset class for training mastering AI models.
    
    Handles loading and preprocessing of audio features and target parameters.
    """
    
    def __init__(
        self,
        features_data: List[torch.Tensor],
        targets_data: List[Dict[str, torch.Tensor]],
        transform: Optional[callable] = None
    ):
        self.features_data = features_data
        self.targets_data = targets_data
        self.transform = transform
        
        assert len(features_data) == len(targets_data), "Features and targets must have same length"
    
    def __len__(self) -> int:
        return len(self.features_data)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        features = self.features_data[idx]
        targets = self.targets_data[idx]
        
        if self.transform:
            features = self.transform(features)
        
        return features, targets


def create_model(
    input_features: int = 128,
    hidden_dim: int = 512,
    num_genres: int = 10,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
) -> MasteringAI:
    """
    Factory function to create and initialize a MasteringAI model.
    
    Args:
        input_features: Number of input features
        hidden_dim: Hidden dimension size
        num_genres: Number of genre classes
        device: Device to place the model on
        
    Returns:
        Initialized MasteringAI model
    """
    model = MasteringAI(
        input_features=input_features,
        hidden_dim=hidden_dim,
        num_genres=num_genres
    )
    
    model = model.to(device)
    
    logger.info(f"Created MasteringAI model with {sum(p.numel() for p in model.parameters())} parameters")
    logger.info(f"Model device: {device}")
    
    return model


def calculate_model_size(model: nn.Module) -> Dict[str, Union[int, float]]:
    """
    Calculate model size and parameter statistics.
    
    Args:
        model: PyTorch model
        
    Returns:
        Dictionary with model statistics
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    # Estimate model size in MB (assuming float32)
    model_size_mb = total_params * 4 / (1024 * 1024)
    
    return {
        'total_parameters': total_params,
        'trainable_parameters': trainable_params,
        'model_size_mb': model_size_mb,
        'memory_usage_mb': model_size_mb * 2  # Rough estimate including gradients
    }