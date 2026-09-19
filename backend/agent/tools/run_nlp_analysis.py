"""Agent tool: run_nlp_analysis."""
from agent.tools.permissions import tool_permission
from nlp_engine.embedding_service import EmbeddingService
from nlp_engine.text_classifier import TextClassifier


@tool_permission(roles={"admin", "analyst"})
def run_nlp_analysis(text: str) -> dict:
    """Verilen metin uzerinde NLP analizi calistirir (siniflandirma + embedding).

    Args:
        text: Analiz edilecek haber/iddia metni.

    Returns:
        {
            "label": "gercek"|"sahte"|"belirsiz",
            "confidence": float,
            "scores": dict,
            "embedding_preview": list[float],  # ilk 8 boyut (debug/onizleme icin)
        }

    TODO: `nlp_engine.text_classifier.TextClassifier` gercek bir Turkce
    fine-tune model ile egitildiginde, bu tool gercek siniflandirma sonucu
    dondurecektir. Su an MOCK/heuristic mantik kullanilmaktadir.
    """
    classifier = TextClassifier()
    embedding_service = EmbeddingService()

    classification = classifier.classify(text)
    embedding = embedding_service.embed(text)

    return {
        "label": classification.label,
        "confidence": classification.confidence,
        "scores": classification.scores,
        "embedding_preview": embedding[:8],
    }
