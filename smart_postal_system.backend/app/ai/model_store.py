"""
Model Store Utility
===================

Handles loading, saving, versioning, and managing trained Scikit-learn
models serialized via ``joblib``.
"""

import os
import joblib
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

class ModelStore:
    """
    Utility class for persistence of Scikit-learn models.
    """

    @staticmethod
    def _ensure_dir():
        """Ensure models directory exists."""
        os.makedirs(MODELS_DIR, exist_ok=True)

    @classmethod
    def save_model(cls, name: str, model: Any, version: str = "v1") -> str:
        """
        Saves a trained model to joblib format.
        """
        cls._ensure_dir()
        filename = f"{name}_{version}.joblib"
        filepath = os.path.join(MODELS_DIR, filename)
        joblib.dump(model, filepath)
        logger.info("Saved model %s to %s", name, filepath)
        return filepath

    @classmethod
    def load_model(cls, name: str, version: str = "v1") -> Optional[Any]:
        """
        Loads a serialized model. Returns None if it does not exist.
        """
        filename = f"{name}_{version}.joblib"
        filepath = os.path.join(MODELS_DIR, filename)
        if not os.path.exists(filepath):
            logger.warning("Model file not found: %s", filepath)
            return None
        try:
            model = joblib.load(filepath)
            logger.info("Loaded model %s from %s", name, filepath)
            return model
        except Exception as e:
            logger.error("Failed to load model %s: %s", name, e)
            return None
