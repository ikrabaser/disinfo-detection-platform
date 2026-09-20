"""
Türkçe misinformation sınıflandırma servisi.

Yerel fine-tuned BERTurk modeli mevcutsa gerçek Transformer inference
çalıştırılır. Model bulunamazsa geliştirme ortamında heuristic fallback
kullanılır.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ClassificationResult:
    label: str
    confidence: float
    scores: dict[str, float] = field(
        default_factory=dict
    )


class TextClassifier:
    DEFAULT_MODEL_PATH = (
        Path(__file__).resolve().parent.parent
        / "ml_models"
        / "berturk-mide22"
    )

    LABELS = [
        "gercek",
        "sahte",
        "belirsiz",
    ]

    def __init__(
        self,
        model_path: str | None = None,
    ):
        env_model_path = os.getenv(
            "NLP_MODEL_PATH",
            "",
        ).strip()

        self.model_path = Path(
            model_path
            or env_model_path
            or self.DEFAULT_MODEL_PATH
        )

        self._model = None
        self._tokenizer = None
        self._torch = None

    @property
    def engine_name(self) -> str:
        if self.has_local_model:
            return "berturk-transformer"

        return "heuristic-fallback"

    @property
    def has_local_model(self) -> bool:
        return (
            self.model_path.exists()
            and (
                self.model_path
                / "config.json"
            ).exists()
        )

    def _load_model(self) -> None:
        if self._model is not None:
            return

        if not self.has_local_model:
            raise FileNotFoundError(
                "Fine-tuned NLP modeli bulunamadı: "
                f"{self.model_path}"
            )

        import torch
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )

        self._torch = torch

        self._tokenizer = (
            AutoTokenizer.from_pretrained(
                self.model_path
            )
        )

        self._model = (
            AutoModelForSequenceClassification
            .from_pretrained(
                self.model_path
            )
        )

        self._model.eval()

    def _classify_transformer(
        self,
        text: str,
    ) -> ClassificationResult:
        self._load_model()

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=256,
        )

        with self._torch.no_grad():
            outputs = self._model(
                **inputs
            )

            probabilities = (
                self._torch.softmax(
                    outputs.logits,
                    dim=-1,
                )[0]
            )

        predicted_id = int(
            self._torch.argmax(
                probabilities
            ).item()
        )

        model_labels = {
            int(key): value
            for key, value
            in self._model.config.id2label.items()
        }

        label = model_labels.get(
            predicted_id,
            self.LABELS[predicted_id],
        )

        scores = {
            model_labels.get(
                index,
                self.LABELS[index],
            ): round(
                float(score),
                4,
            )
            for index, score
            in enumerate(
                probabilities.tolist()
            )
        }

        confidence = float(
            probabilities[
                predicted_id
            ].item()
        )

        return ClassificationResult(
            label=label,
            confidence=round(
                confidence,
                4,
            ),
            scores=scores,
        )

    def _classify_heuristic(
        self,
        text: str,
    ) -> ClassificationResult:
        lowered = text.lower()

        suspicious_markers = [
            "!!!",
            "paylaşmadan geçme",
            "inanılmaz",
            "şok",
        ]

        suspicious_hits = sum(
            marker in lowered
            for marker
            in suspicious_markers
        )

        if suspicious_hits >= 2:
            label = "sahte"
            confidence = 0.82

        elif suspicious_hits == 1:
            label = "belirsiz"
            confidence = 0.55

        else:
            label = "gercek"
            confidence = 0.70

        scores = {
            "gercek": (
                confidence
                if label == "gercek"
                else 1 - confidence
            ),
            "sahte": (
                confidence
                if label == "sahte"
                else 1 - confidence
            ),
            "belirsiz": (
                confidence
                if label == "belirsiz"
                else 0.0
            ),
        }

        return ClassificationResult(
            label=label,
            confidence=confidence,
            scores=scores,
        )

    def classify(
        self,
        text: str,
    ) -> ClassificationResult:
        text = text.strip()

        if not text:
            return ClassificationResult(
                label="belirsiz",
                confidence=0.0,
                scores={
                    "gercek": 0.0,
                    "sahte": 0.0,
                    "belirsiz": 1.0,
                },
            )

        if self.has_local_model:
            return (
                self._classify_transformer(
                    text
                )
            )

        return self._classify_heuristic(
            text
        )
