"""
scikit-learn tabanli yardimci fonksiyonlar (ör. klasik ML ozellikleri,
TF-IDF, kume analizleri). Agir olmayan bir bagimlilik olsa da yine de
lazy-import kullanilir, tutarlilik icin.
"""
from __future__ import annotations


def tfidf_keywords(texts: list[str], top_k: int = 5) -> list[list[str]]:
    """Her metin icin en yuksek TF-IDF skorlu kelimeleri doner (stub/mock).

    TODO: gercek implementasyon icin sklearn.feature_extraction.text.TfidfVectorizer
    kullanilmalidir:

        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(max_features=1000)
        matrix = vectorizer.fit_transform(texts)
        ...
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer

        vectorizer = TfidfVectorizer(max_features=50)
        matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        results = []
        for row in matrix.toarray():
            top_indices = row.argsort()[::-1][:top_k]
            results.append([feature_names[i] for i in top_indices if row[i] > 0])
        return results
    except ImportError:
        # scikit-learn kurulu degilse basit bir mock doner.
        return [text.split()[:top_k] for text in texts]
