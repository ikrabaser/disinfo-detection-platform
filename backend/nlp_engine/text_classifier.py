"""
TextClassifier - Turkce metinlerde sahte haber/manipulatif icerik
siniflandirmasi icin arayuz.

Gercek implementasyon Hugging Face Transformers (ör. bir Turkce BERT/
BERTurk fine-tune modeli) kullanmalidir. Agir bagimliliklar (`torch`,
`transformers`) modul yuklenirken DEGIL, sadece gerceke inference
cagrildiginda (lazy-import) import edilir; boylece bu dosya bu kutuphaneler
kurulu olmadan da import edilebilir.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ClassificationResult:
    label: str  # "gercek" | "sahte" | "belirsiz"
    confidence: float
    scores: dict = field(default_factory=dict)


class TextClassifier:
    """Turkce metin siniflandirma servisi (sahte haber / manipulatif icerik).

    TODO (gercek implementasyon):
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
    """

    DEFAULT_MODEL_NAME = "dbmdz/bert-base-turkish-cased"  # ornek, fine-tune edilmemis

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or self.DEFAULT_MODEL_NAME
        self._model = None  # lazy-init
        self._tokenizer = None  # lazy-init

    def _load_model(self):
        """Gercek transformers modelini lazy-import ile yukler (TODO)."""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        except ImportError as exc:
            raise ImportError(
                "transformers/torch kurulu degil. Gercek siniflandirma icin "
                "requirements.txt icindeki ML bagimliliklarini kurun."
            ) from exc

    def classify(self, text: str) -> ClassificationResult:
        """Verilen metni siniflandirir.

        Su an MOCK bir sonuc doner (deterministik olmayan gercek bir model
        egitilmedigi icin). Gercek implementasyonda `self._load_model()`
        cagrilip tokenizer + model ile inference yapilmalidir.
        """
        # --- MOCK LOGIC (TODO: gercek inference ile degistir) ---
        lowered = text.lower()
        suspicious_markers = ["!!!", "paylaşmadan geçme", "inanılmaz", "şok"]
        suspicious_hits = sum(marker in lowered for marker in suspicious_markers)
        if suspicious_hits >= 2:
            label, confidence = "sahte", 0.82
        elif suspicious_hits == 1:
            label, confidence = "belirsiz", 0.55
        else:
            label, confidence = "gercek", 0.70

        return ClassificationResult(
            label=label,
            confidence=confidence,
            scores={"gercek": 1 - confidence if label != "gercek" else confidence,
                    "sahte": confidence if label == "sahte" else 1 - confidence},
        )
