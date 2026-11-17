"""ONNX-backed image analysis for grievance evidence.

Two models are loaded lazily from ``ml/artifacts/vision``:

* ``issue_classifier.onnx`` — pothole / garbage / other (water_leak optional)
* ``ai_image_detector.onnx`` — real / fake

The service is intentionally defensive: if the models or ``onnxruntime`` are
missing, the rest of the grievance workflow must continue normally.
"""

from __future__ import annotations

import base64
import io
import json
import logging
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image, ImageOps

from backend.config import Config

logger = logging.getLogger(__name__)

try:  # Pillow >= 9.1
    _BILINEAR = Image.Resampling.BILINEAR
except AttributeError:  # pragma: no cover - older Pillow
    _BILINEAR = Image.BILINEAR


ISSUE_DEPARTMENT_MAP = {
    'pothole': 'Roads and Public Works',
    'garbage': 'Sanitation and Waste Management',
    'water_leak': 'Water Supply',
}

ISSUE_LABELS = {
    'pothole': 'Pothole / road damage',
    'garbage': 'Garbage / litter',
    'water_leak': 'Water leakage',
    'other': 'No clear issue',
}


class ImageAIService:
    """Run the exported CNN models on base64-encoded complaint images."""

    def __init__(self, model_dir: Optional[str] = None):
        explicit_model_dir = bool(model_dir)
        self.model_dir = Path(
            model_dir
            or getattr(Config, 'VISION_MODEL_DIR', '')
            or (Path(__file__).resolve().parents[2] / 'ml' / 'artifacts' / 'vision')
        )
        self.issue_model_path = Path(
            self.model_dir / 'issue_classifier.onnx'
            if explicit_model_dir
            else getattr(
                Config,
                'VISION_ISSUE_MODEL_PATH',
                self.model_dir / 'issue_classifier.onnx',
            )
        )
        self.ai_model_path = Path(
            self.model_dir / 'ai_image_detector.onnx'
            if explicit_model_dir
            else getattr(
                Config,
                'VISION_AI_MODEL_PATH',
                self.model_dir / 'ai_image_detector.onnx',
            )
        )

        self._sessions: Dict[str, Any] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
        self._load_error: Optional[str] = None
        self._lock = Lock()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def is_enabled(self) -> bool:
        return bool(getattr(Config, 'ENABLE_VISION_ANALYSIS', True))

    def _load(self) -> bool:
        if not self.is_enabled():
            self._load_error = 'Vision analysis is disabled.'
            return False

        if self._loaded:
            return self._load_error is None

        with self._lock:
            if self._loaded:
                return self._load_error is None

            self._loaded = True

            try:
                import onnxruntime as ort
            except Exception as exc:  # pragma: no cover - dependency issue
                self._load_error = f'onnxruntime is not available: {exc}'
                return False

            for key, path in (
                ('issue', self.issue_model_path),
                ('ai', self.ai_model_path),
            ):
                if not path.exists():
                    self._load_error = f'Missing vision model: {path}'
                    return False

                try:
                    self._sessions[key] = ort.InferenceSession(
                        str(path),
                        providers=['CPUExecutionProvider'],
                    )
                except Exception as exc:
                    self._load_error = f'Could not load {path.name}: {exc}'
                    return False

            try:
                self._configs['issue'] = self._read_json(
                    self.model_dir / 'issue_classifier_preprocess.json'
                )
                self._configs['ai'] = self._read_json(
                    self.model_dir / 'ai_image_detector_preprocess.json'
                )
            except Exception as exc:
                self._load_error = f'Could not load vision preprocessing config: {exc}'
                return False

        return True

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as fh:
            return json.load(fh)

    # ------------------------------------------------------------------
    # Preprocessing / inference
    # ------------------------------------------------------------------

    @staticmethod
    def _decode_image(image_data: Any) -> Image.Image:
        if not isinstance(image_data, str) or not image_data.strip():
            raise ValueError('Image must be a base64 data URL or base64 string.')

        payload = image_data.split(',', 1)[1] if ',' in image_data else image_data
        raw = base64.b64decode(payload, validate=False)
        image = Image.open(io.BytesIO(raw))
        image = ImageOps.exif_transpose(image)
        return image.convert('RGB')

    @staticmethod
    def _prepare(image: Image.Image, cfg: Dict[str, Any]) -> np.ndarray:
        size = int(cfg['img_size'])
        mean = np.asarray(cfg['mean'], dtype=np.float32)
        std = np.asarray(cfg['std'], dtype=np.float32)

        resized = image.resize((size, size), _BILINEAR)
        arr = np.asarray(resized, dtype=np.float32) / 255.0
        arr = (arr - mean) / std
        arr = np.transpose(arr, (2, 0, 1))[None, ...]
        return arr.astype(np.float32)

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        logits = np.asarray(logits, dtype=np.float32).reshape(-1)
        shifted = logits - np.max(logits)
        exp = np.exp(shifted)
        return exp / max(float(exp.sum()), 1e-12)

    def _run(self, key: str, array: np.ndarray) -> np.ndarray:
        cfg = self._configs[key]
        session = self._sessions[key]
        input_name = cfg.get('input_name', 'input')
        return session.run(None, {input_name: array})[0][0]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        self._load()
        return {
            'enabled': self.is_enabled(),
            'available': self._load_error is None,
            'reason': self._load_error,
            'model_dir': str(self.model_dir),
            'issue_model': str(self.issue_model_path),
            'ai_model': str(self.ai_model_path),
        }

    def analyze_base64_image(self, image_data: Any) -> Dict[str, Any]:
        if not self._load():
            return {'available': False, 'reason': self._load_error}

        try:
            image = self._decode_image(image_data)

            issue_cfg = self._configs['issue']
            ai_cfg = self._configs['ai']

            issue_probs = self._softmax(
                self._run('issue', self._prepare(image, issue_cfg))
            )
            ai_probs = self._softmax(
                self._run('ai', self._prepare(image, ai_cfg))
            )

            issue_classes = list(issue_cfg['classes'])
            ai_classes = list(ai_cfg['classes'])

            issue_scores = {
                label: round(float(prob), 6)
                for label, prob in zip(issue_classes, issue_probs)
            }
            ai_scores = {
                label: round(float(prob), 6)
                for label, prob in zip(ai_classes, ai_probs)
            }

            issue_label = max(issue_scores, key=issue_scores.get)
            ai_label = max(ai_scores, key=ai_scores.get)
            ai_fake_prob = float(ai_scores.get('fake', 0.0))
            threshold = float(getattr(Config, 'VISION_AI_FLAG_THRESHOLD', 0.80))

            return {
                'available': True,
                'issue_type': issue_label,
                'issue_display': ISSUE_LABELS.get(issue_label, issue_label),
                'issue_confidence': round(float(issue_scores[issue_label]), 4),
                'issue_confidence_pct': round(
                    float(issue_scores[issue_label]) * 100, 2
                ),
                'issue_scores': issue_scores,
                'issue_department': ISSUE_DEPARTMENT_MAP.get(issue_label),
                'ai_label': ai_label,
                'ai_generated': ai_fake_prob >= threshold,
                'ai_confidence': round(ai_fake_prob, 4),
                'ai_confidence_pct': round(ai_fake_prob * 100, 2),
                'ai_scores': ai_scores,
                'ai_flag_threshold_pct': round(threshold * 100, 2),
            }
        except Exception as exc:
            logger.warning('Image analysis failed: %s', exc)
            return {
                'available': False,
                'reason': f'Image analysis failed: {exc}',
            }

    def analyze_images(self, images: Any) -> Dict[str, Any]:
        """Analyze up to five evidence images and aggregate the results."""
        if not self.is_enabled():
            return {'available': False, 'reason': 'Vision analysis is disabled.'}

        if not images:
            return {'available': False, 'reason': 'No images supplied.'}

        if not isinstance(images, (list, tuple)):
            images = [images]
        else:
            images = list(images)

        per_image: List[Dict[str, Any]] = []
        for index, image_data in enumerate(images[:5], start=1):
            result = self.analyze_base64_image(image_data)
            result['image_index'] = index
            per_image.append(result)

        valid = [item for item in per_image if item.get('available')]
        if not valid:
            reason = per_image[0].get('reason') if per_image else 'Analysis failed.'
            return {
                'available': False,
                'reason': reason,
                'per_image': per_image,
            }

        # Prefer a concrete issue over "other" when both are present.
        issue_candidates = [
            item for item in valid if item.get('issue_type') != 'other'
        ] or valid
        best_issue = max(
            issue_candidates,
            key=lambda item: float(item.get('issue_confidence', 0.0)),
        )

        best_ai = max(
            valid,
            key=lambda item: float(item.get('ai_confidence', 0.0)),
        )

        ai_confidence = float(best_ai.get('ai_confidence', 0.0))
        threshold = float(getattr(Config, 'VISION_AI_FLAG_THRESHOLD', 0.80))
        ai_generated = ai_confidence >= threshold

        issue_confidence = float(best_issue.get('issue_confidence', 0.0))
        issue_threshold = float(
            getattr(Config, 'VISION_ISSUE_CONFIDENCE_THRESHOLD', 0.60)
        )
        suggested_department = (
            best_issue.get('issue_department')
            if issue_confidence >= issue_threshold
            else None
        )

        if ai_generated:
            recommendation = (
                'Authenticity warning: the image may be AI-generated. '
                'Use it as supporting evidence only and verify manually.'
            )
        elif suggested_department:
            recommendation = (
                f'Image suggests {best_issue.get("issue_display", best_issue["issue_type"])}. '
                'Text routing remains the primary signal.'
            )
        elif best_issue.get('issue_type') == 'other':
            recommendation = (
                'No clear civic issue was detected in the image. '
                'Text routing remains the primary signal.'
            )
        else:
            recommendation = (
                'Image issue confidence is below the department-suggestion threshold. '
                'Text routing remains the primary signal.'
            )

        return {
            'available': True,
            'model_version': 'colab-cnn-v1',
            'images_requested': len(images),
            'images_analyzed': len(valid),
            'issue_type': best_issue.get('issue_type'),
            'issue_display': best_issue.get('issue_display'),
            'issue_confidence': best_issue.get('issue_confidence'),
            'issue_confidence_pct': best_issue.get('issue_confidence_pct'),
            'issue_scores': best_issue.get('issue_scores', {}),
            'issue_department': suggested_department,
            'issue_confidence_threshold_pct': round(issue_threshold * 100, 2),
            'ai_label': 'fake' if ai_generated else 'real',
            'ai_generated': ai_generated,
            'ai_confidence': round(ai_confidence, 4),
            'ai_confidence_pct': round(ai_confidence * 100, 2),
            'ai_scores': best_ai.get('ai_scores', {}),
            'ai_flag_threshold_pct': round(threshold * 100, 2),
            'recommendation': recommendation,
            'per_image': per_image,
        }


image_ai_service = ImageAIService()
