import json
import os
from datetime import datetime

import joblib

from backend.config import Config
from backend.utils.text_clean import clean_text


class GrievanceClassifier:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.loaded = False
        self.loaded_at = None
        self.training_metadata = None

    def _load_training_metadata(self):
        if not os.path.exists(Config.MODEL_METADATA_PATH):
            self.training_metadata = None
            return
        try:
            with open(Config.MODEL_METADATA_PATH, 'r', encoding='utf-8') as metadata_file:
                self.training_metadata = json.load(metadata_file)
        except Exception:
            self.training_metadata = None

    def load_model(self):
        """Load the trained model and vectorizer."""
        try:
            if os.path.exists(Config.MODEL_PATH) and os.path.exists(Config.VECTORIZER_PATH):
                self.model = joblib.load(Config.MODEL_PATH)
                self.vectorizer = joblib.load(Config.VECTORIZER_PATH)
                self.loaded = True
                self.loaded_at = datetime.utcnow()
                self._load_training_metadata()
                print("[OK] ML Model and Vectorizer loaded successfully")
            else:
                print("[WARN] ML Model not found. Please run ml/train.py first")
                self.loaded = False
                self.loaded_at = None
                self.training_metadata = None
        except Exception as e:
            print(f"[ERROR] Error loading ML model: {e}")
            self.loaded = False
            self.loaded_at = None
            self.training_metadata = None

    def predict_with_confidence(self, complaint_text):
        """
        Predict department and confidence for a complaint.
        Confidence is a 0-1 float based on model probabilities when available.
        """
        default_dept = getattr(Config, 'DEFAULT_DEPARTMENT', 'Roads and Public Works')
        fallback = {
            'department': default_dept,
            'confidence': 0.0,
            'top_candidates': [{'department': default_dept, 'confidence': 0.0}],
            'model_loaded': False,
            'source': 'fallback'
        }

        if not self.loaded:
            print("⚠ Model not loaded, returning default department")
            return fallback

        try:
            cleaned_text = clean_text(complaint_text or '')
            text_vectorized = self.vectorizer.transform([cleaned_text])
            prediction = self.model.predict(text_vectorized)[0]

            top_candidates = []
            confidence = 0.0

            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(text_vectorized)[0]
                classes = list(getattr(self.model, 'classes_', []))
                ranked = sorted(
                    zip(classes, probabilities),
                    key=lambda pair: pair[1],
                    reverse=True
                )
                top_candidates = [
                    {'department': str(label), 'confidence': float(prob)}
                    for label, prob in ranked[:3]
                ]
                confidence = float(top_candidates[0]['confidence']) if top_candidates else 0.0
            else:
                top_candidates = [{'department': str(prediction), 'confidence': 1.0}]
                confidence = 1.0

            return {
                'department': str(prediction),
                'confidence': max(0.0, min(1.0, confidence)),
                'top_candidates': top_candidates,
                'model_loaded': True,
                'source': 'ml'
            }
        except Exception as e:
            print(f"✗ Error predicting department: {e}")
            return fallback

    def predict(self, complaint_text):
        """
        Backward-compatible prediction helper.
        Returns department name or 'General' if prediction fails.
        """
        return self.predict_with_confidence(complaint_text)['department']

    def get_runtime_status(self):
        """Expose model runtime state for admin diagnostics."""
        return {
            'model_loaded': self.loaded,
            'loaded_at_utc': self.loaded_at.isoformat() if self.loaded_at else None,
            'artifacts': {
                'model_path': Config.MODEL_PATH,
                'model_exists': os.path.exists(Config.MODEL_PATH),
                'vectorizer_path': Config.VECTORIZER_PATH,
                'vectorizer_exists': os.path.exists(Config.VECTORIZER_PATH),
                'metadata_path': Config.MODEL_METADATA_PATH,
                'metadata_exists': os.path.exists(Config.MODEL_METADATA_PATH),
            },
            'label_classes': (
                [str(label) for label in getattr(self.model, 'classes_', [])]
                if self.loaded and hasattr(self.model, 'classes_')
                else []
            ),
            'training_metadata': self.training_metadata,
        }

# Global classifier instance
classifier = GrievanceClassifier()
