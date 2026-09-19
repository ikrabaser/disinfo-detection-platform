from nlp_engine.embedding_service import EmbeddingService
from nlp_engine.text_classifier import TextClassifier


def test_text_classifier_returns_result_with_label():
    classifier = TextClassifier()
    result = classifier.classify("Bu haber tamamen gercek ve dogrulanmis bir kaynaga dayaniyor.")
    assert result.label in {"gercek", "sahte", "belirsiz"}
    assert 0.0 <= result.confidence <= 1.0


def test_text_classifier_flags_suspicious_markers():
    classifier = TextClassifier()
    result = classifier.classify("ŞOK!!! Paylaşmadan geçme, inanılmaz bir gelişme!!!")
    assert result.label == "sahte"


def test_embedding_service_returns_fixed_dimension_vector():
    service = EmbeddingService()
    vector = service.embed("test metni")
    assert len(vector) == EmbeddingService.EMBEDDING_DIM
    assert all(0.0 <= v <= 1.0 for v in vector)


def test_embedding_service_identical_text_has_similarity_one():
    service = EmbeddingService()
    sim = service.similarity("ayni metin", "ayni metin")
    assert sim == 1.0
