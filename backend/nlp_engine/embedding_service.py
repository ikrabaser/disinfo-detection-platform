"""
EmbeddingService - metinleri semantik vektorlere (embedding) ceviren servis.

Gercek implementasyon Sentence Transformers (ör. `paraphrase-multilingual-
MiniLM-L12-v2` gibi Turkce'yi de destekleyen bir model) kullanmalidir.
Agir bagimliliklar lazy-import edilir.
"""
from __future__ import annotations

import hashlib


class EmbeddingService:
    """Metin -> embedding vektoru servisi (semantik benzerlik/arama icin).

    TODO (gercek implementasyon):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(self.model_name)
        return self._model.encode(text).tolist()
    """

    DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIM = 384

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or self.DEFAULT_MODEL_NAME
        self._model = None  # lazy-init

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers kurulu degil. Gercek embedding icin "
                "requirements.txt icindeki ML bagimliliklarini kurun."
            ) from exc

    def embed(self, text: str) -> list[float]:
        """Metni sabit boyutlu (mock) bir embedding vektorune cevirir.

        MOCK: gercek bir model calistirmak yerine, metnin hash'inden
        deterministik ama anlamsiz bir vektor uretir. Sadece arayuzun
        (interface) dogru sekli/tipi dondugunu garanti etmek icindir.
        """
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # digest 32 byte -> tekrar ederek EMBEDDING_DIM boyutuna tamamla
        repeated = (digest * ((self.EMBEDDING_DIM // len(digest)) + 1))[: self.EMBEDDING_DIM]
        return [b / 255.0 for b in repeated]

    def similarity(self, text_a: str, text_b: str) -> float:
        """Iki metin arasindaki kosinus benzerligi (mock embedding uzerinden)."""
        vec_a = self.embed(text_a)
        vec_b = self.embed(text_b)
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
