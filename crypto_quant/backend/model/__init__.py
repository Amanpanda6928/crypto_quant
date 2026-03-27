"""
Model module for training and prediction.

Handles:
- Model training (multi-horizon classification)
- Real-time prediction
"""

from .train import MultiHorizonTrainer, train_model
from .predict import Predictor, get_current_prediction, get_all_predictions

__all__ = [
    "MultiHorizonTrainer",
    "train_model",
    "Predictor",
    "get_current_prediction",
]