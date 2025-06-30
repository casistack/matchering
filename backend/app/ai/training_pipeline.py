"""
Training Pipeline for AI Mastering Models.

This module implements the training pipeline for the CNN-LSTM hybrid neural network,
including data loading, training loops, validation, and model optimization.
"""

import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torch.utils.tensorboard import SummaryWriter
import torch.nn.functional as F
from tqdm import tqdm

from .mastering_model import MasteringAI, MasteringLoss, MasteringDataset, calculate_model_size
from .feature_extractor import AudioFeatureExtractor

logger = logging.getLogger(__name__)


class TrainingConfig:
    """Configuration for training pipeline."""
    
    def __init__(
        self,
        # Model parameters
        input_features: int = 128,
        hidden_dim: int = 512,
        num_genres: int = 10,
        
        # Training parameters
        batch_size: int = 32,
        learning_rate: float = 1e-3,
        num_epochs: int = 100,
        weight_decay: float = 1e-4,
        
        # Data parameters
        train_split: float = 0.8,
        val_split: float = 0.15,
        test_split: float = 0.05,
        
        # Optimization parameters
        patience: int = 10,
        min_delta: float = 1e-4,
        lr_scheduler_factor: float = 0.5,
        lr_scheduler_patience: int = 5,
        
        # Hardware parameters
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        num_workers: int = 4,
        pin_memory: bool = True,
        
        # Logging parameters
        log_interval: int = 10,
        save_interval: int = 5,
        tensorboard_log_dir: str = "logs/tensorboard",
        model_save_dir: str = "models/checkpoints"
    ):
        self.input_features = input_features
        self.hidden_dim = hidden_dim
        self.num_genres = num_genres
        
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        self.weight_decay = weight_decay
        
        self.train_split = train_split
        self.val_split = val_split
        self.test_split = test_split
        
        self.patience = patience
        self.min_delta = min_delta
        self.lr_scheduler_factor = lr_scheduler_factor
        self.lr_scheduler_patience = lr_scheduler_patience
        
        self.device = device
        self.num_workers = num_workers
        self.pin_memory = pin_memory and device == "cuda"
        
        self.log_interval = log_interval
        self.save_interval = save_interval
        self.tensorboard_log_dir = tensorboard_log_dir
        self.model_save_dir = model_save_dir
        
        # Create directories
        Path(self.tensorboard_log_dir).mkdir(parents=True, exist_ok=True)
        Path(self.model_save_dir).mkdir(parents=True, exist_ok=True)


class EarlyStopping:
    """Early stopping utility to prevent overfitting."""
    
    def __init__(self, patience: int = 10, min_delta: float = 1e-4):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_score = None
        self.early_stop = False
    
    def __call__(self, val_loss: float) -> bool:
        score = -val_loss
        
        if self.best_score is None:
            self.best_score = score
        elif score < self.best_score + self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.counter = 0
        
        return self.early_stop


class ModelTrainer:
    """Main trainer class for the mastering AI model."""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.device = torch.device(config.device)
        
        # Initialize model
        self.model = MasteringAI(
            input_features=config.input_features,
            hidden_dim=config.hidden_dim,
            num_genres=config.num_genres
        ).to(self.device)
        
        # Initialize loss function
        self.criterion = MasteringLoss()
        
        # Initialize optimizer
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )
        
        # Initialize learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=config.lr_scheduler_factor,
            patience=config.lr_scheduler_patience,
            verbose=True
        )
        
        # Initialize early stopping
        self.early_stopping = EarlyStopping(
            patience=config.patience,
            min_delta=config.min_delta
        )
        
        # Initialize tensorboard writer
        self.writer = SummaryWriter(config.tensorboard_log_dir)
        
        # Training state
        self.current_epoch = 0
        self.best_val_loss = float('inf')
        self.train_losses = []
        self.val_losses = []
        
        logger.info(f"Initialized ModelTrainer with device: {self.device}")
        model_stats = calculate_model_size(self.model)
        logger.info(f"Model statistics: {model_stats}")
    
    def prepare_data(
        self,
        features_data: List[torch.Tensor],
        targets_data: List[Dict[str, torch.Tensor]]
    ) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """
        Prepare data loaders for training, validation, and testing.
        
        Args:
            features_data: List of feature tensors
            targets_data: List of target dictionaries
            
        Returns:
            Tuple of (train_loader, val_loader, test_loader)
        """
        dataset = MasteringDataset(features_data, targets_data)
        
        # Calculate split sizes
        total_size = len(dataset)
        train_size = int(self.config.train_split * total_size)
        val_size = int(self.config.val_split * total_size)
        test_size = total_size - train_size - val_size
        
        # Split dataset
        train_dataset, val_dataset, test_dataset = random_split(
            dataset, [train_size, val_size, test_size]
        )
        
        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=self.config.num_workers,
            pin_memory=self.config.pin_memory
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=self.config.num_workers,
            pin_memory=self.config.pin_memory
        )
        
        test_loader = DataLoader(
            test_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=self.config.num_workers,
            pin_memory=self.config.pin_memory
        )
        
        logger.info(f"Data splits - Train: {train_size}, Val: {val_size}, Test: {test_size}")
        
        return train_loader, val_loader, test_loader
    
    def train_epoch(self, train_loader: DataLoader) -> Dict[str, float]:
        """Train the model for one epoch."""
        self.model.train()
        
        total_loss = 0.0
        loss_components = {
            'genre_loss': 0.0,
            'eq_loss': 0.0,
            'compression_loss': 0.0,
            'stereo_loss': 0.0,
            'limiting_loss': 0.0,
            'confidence_loss': 0.0
        }
        
        progress_bar = tqdm(train_loader, desc=f"Epoch {self.current_epoch + 1}")
        
        for batch_idx, (features, targets) in enumerate(progress_bar):
            # Move data to device
            features = features.to(self.device)
            targets = {k: v.to(self.device) for k, v in targets.items()}
            
            # Forward pass
            self.optimizer.zero_grad()
            predictions = self.model(features)
            
            # Compute loss
            losses = self.criterion(predictions, targets)
            total_batch_loss = losses['total_loss']
            
            # Backward pass
            total_batch_loss.backward()
            
            # Gradient clipping to prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            # Update running losses
            total_loss += total_batch_loss.item()
            for key in loss_components:
                if key in losses:
                    loss_components[key] += losses[key].item()
            
            # Update progress bar
            progress_bar.set_postfix({
                'loss': f"{total_batch_loss.item():.4f}",
                'lr': f"{self.optimizer.param_groups[0]['lr']:.6f}"
            })
            
            # Log to tensorboard
            if batch_idx % self.config.log_interval == 0:
                step = self.current_epoch * len(train_loader) + batch_idx
                self.writer.add_scalar('Train/BatchLoss', total_batch_loss.item(), step)
                for key, value in losses.items():
                    self.writer.add_scalar(f'Train/{key}', value.item(), step)
        
        # Calculate average losses
        avg_loss = total_loss / len(train_loader)
        avg_components = {k: v / len(train_loader) for k, v in loss_components.items()}
        
        return {'total_loss': avg_loss, **avg_components}
    
    def validate_epoch(self, val_loader: DataLoader) -> Dict[str, float]:
        """Validate the model for one epoch."""
        self.model.eval()
        
        total_loss = 0.0
        loss_components = {
            'genre_loss': 0.0,
            'eq_loss': 0.0,
            'compression_loss': 0.0,
            'stereo_loss': 0.0,
            'limiting_loss': 0.0,
            'confidence_loss': 0.0
        }
        
        with torch.no_grad():
            for features, targets in tqdm(val_loader, desc="Validation"):
                # Move data to device
                features = features.to(self.device)
                targets = {k: v.to(self.device) for k, v in targets.items()}
                
                # Forward pass
                predictions = self.model(features)
                
                # Compute loss
                losses = self.criterion(predictions, targets)
                
                # Update running losses
                total_loss += losses['total_loss'].item()
                for key in loss_components:
                    if key in losses:
                        loss_components[key] += losses[key].item()
        
        # Calculate average losses
        avg_loss = total_loss / len(val_loader)
        avg_components = {k: v / len(val_loader) for k, v in loss_components.items()}
        
        return {'total_loss': avg_loss, **avg_components}
    
    def save_checkpoint(
        self,
        epoch: int,
        val_loss: float,
        is_best: bool = False
    ):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'val_loss': val_loss,
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'config': self.config
        }
        
        # Save regular checkpoint
        checkpoint_path = Path(self.config.model_save_dir) / f"checkpoint_epoch_{epoch}.pth"
        torch.save(checkpoint, checkpoint_path)
        
        # Save best model
        if is_best:
            best_path = Path(self.config.model_save_dir) / "best_model.pth"
            torch.save(checkpoint, best_path)
            logger.info(f"Saved best model with validation loss: {val_loss:.4f}")
        
        logger.info(f"Saved checkpoint: {checkpoint_path}")
    
    def load_checkpoint(self, checkpoint_path: str) -> Dict:
        """Load model checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
        self.current_epoch = checkpoint['epoch']
        self.train_losses = checkpoint.get('train_losses', [])
        self.val_losses = checkpoint.get('val_losses', [])
        
        logger.info(f"Loaded checkpoint from epoch {self.current_epoch}")
        return checkpoint
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        resume_from: Optional[str] = None
    ) -> Dict[str, List[float]]:
        """
        Main training loop.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            resume_from: Path to checkpoint to resume from
            
        Returns:
            Training history
        """
        if resume_from:
            self.load_checkpoint(resume_from)
        
        logger.info("Starting training...")
        start_time = time.time()
        
        for epoch in range(self.current_epoch, self.config.num_epochs):
            self.current_epoch = epoch
            
            # Training phase
            train_losses = self.train_epoch(train_loader)
            self.train_losses.append(train_losses['total_loss'])
            
            # Validation phase
            val_losses = self.validate_epoch(val_loader)
            val_loss = val_losses['total_loss']
            self.val_losses.append(val_loss)
            
            # Learning rate scheduling
            self.scheduler.step(val_loss)
            
            # Log to tensorboard
            self.writer.add_scalar('Train/EpochLoss', train_losses['total_loss'], epoch)
            self.writer.add_scalar('Val/EpochLoss', val_loss, epoch)
            self.writer.add_scalar('Learning_Rate', self.optimizer.param_groups[0]['lr'], epoch)
            
            # Log training components
            for key, value in train_losses.items():
                if key != 'total_loss':
                    self.writer.add_scalar(f'Train/{key}', value, epoch)
            
            # Log validation components
            for key, value in val_losses.items():
                if key != 'total_loss':
                    self.writer.add_scalar(f'Val/{key}', value, epoch)
            
            # Check for best model
            is_best = val_loss < self.best_val_loss
            if is_best:
                self.best_val_loss = val_loss
            
            # Save checkpoint
            if epoch % self.config.save_interval == 0 or is_best:
                self.save_checkpoint(epoch, val_loss, is_best)
            
            # Early stopping check
            if self.early_stopping(val_loss):
                logger.info(f"Early stopping triggered at epoch {epoch}")
                break
            
            # Log progress
            logger.info(
                f"Epoch {epoch + 1}/{self.config.num_epochs} - "
                f"Train Loss: {train_losses['total_loss']:.4f}, "
                f"Val Loss: {val_loss:.4f}, "
                f"LR: {self.optimizer.param_groups[0]['lr']:.6f}"
            )
        
        training_time = time.time() - start_time
        logger.info(f"Training completed in {training_time:.2f} seconds")
        
        # Save final model
        self.save_checkpoint(self.current_epoch, val_loss, is_best=True)
        
        # Close tensorboard writer
        self.writer.close()
        
        return {
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'best_val_loss': self.best_val_loss,
            'training_time': training_time
        }
    
    def evaluate(self, test_loader: DataLoader) -> Dict[str, float]:
        """Evaluate the model on test data."""
        logger.info("Evaluating model...")
        
        self.model.eval()
        test_losses = self.validate_epoch(test_loader)
        
        # Additional evaluation metrics can be added here
        # (e.g., accuracy for genre classification, MAE for parameters)
        
        logger.info(f"Test Results: {test_losses}")
        return test_losses


def train_mastering_model(
    features_data: List[torch.Tensor],
    targets_data: List[Dict[str, torch.Tensor]],
    config: Optional[TrainingConfig] = None,
    resume_from: Optional[str] = None
) -> Tuple[MasteringAI, Dict[str, List[float]]]:
    """
    Convenience function to train a mastering model.
    
    Args:
        features_data: Training features
        targets_data: Training targets
        config: Training configuration
        resume_from: Checkpoint to resume from
        
    Returns:
        Tuple of (trained_model, training_history)
    """
    if config is None:
        config = TrainingConfig()
    
    trainer = ModelTrainer(config)
    
    # Prepare data
    train_loader, val_loader, test_loader = trainer.prepare_data(
        features_data, targets_data
    )
    
    # Train model
    training_history = trainer.train(train_loader, val_loader, resume_from)
    
    # Evaluate on test set
    test_results = trainer.evaluate(test_loader)
    training_history['test_results'] = test_results
    
    return trainer.model, training_history