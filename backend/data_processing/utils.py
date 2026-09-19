"""
Ham sosyal medya/haber verisini pandas DataFrame'lere ceviren yardimci
fonksiyonlar. Bu bir Django app'i DEGILDIR, sade bir Python paketidir;
diger app'ler (agent, graph_engine, nlp_engine) tarafindan import edilir.
"""
from __future__ import annotations

from typing import Any


def posts_to_dataframe(posts: list[dict[str, Any]]):
    """Mock/gercek paylasim listesini pandas DataFrame'e cevirir.

    Args:
        posts: [{"id", "author_id", "text", "created_at", "shared_from_id"}, ...]

    Returns:
        pandas.DataFrame
    """
    import pandas as pd

    if not posts:
        return pd.DataFrame(columns=["id", "author_id", "text", "created_at", "shared_from_id"])
    return pd.DataFrame(posts)


def compute_propagation_speed(df) -> float:
    """Paylasimlarin zaman damgalarindan basit bir yayilim hizi (post/saat) hesaplar (mock/basit).

    TODO: gercek implementasyonda zaman serisi analizleri (ör. ilk N dakikadaki
    paylasim yogunlugu, exponential buyume orani) kullanilmalidir.
    """
    import pandas as pd

    if df.empty or "created_at" not in df.columns:
        return 0.0
    timestamps = pd.to_datetime(df["created_at"], errors="coerce").dropna()
    if timestamps.empty:
        return 0.0
    span_hours = max((timestamps.max() - timestamps.min()).total_seconds() / 3600.0, 1e-6)
    return len(timestamps) / span_hours


def author_share_counts(df):
    """Her yazarin kac paylasim yaptigini sayan bir Series/DataFrame doner."""
    if df.empty or "author_id" not in df.columns:
        import pandas as pd

        return pd.Series(dtype=int)
    return df.groupby("author_id").size().sort_values(ascending=False)
