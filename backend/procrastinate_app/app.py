"""
Procrastinate (Postgres-tabanli async task queue) yapilandirmasi - OPSIYONEL.

Procrastinate, ayri bir worker sureci gerektirdigi ve ek bir bagimlilik
(`procrastinate` paketi + Postgres baglantisi) oldugu icin bu proje
iskeletinde varsayilan olarak DEVRE DISI birakilmistir
(`settings.PROCRASTINATE_ENABLED`).

Aktif etmek icin:
    1. `pip install procrastinate` (requirements.txt icinde yorum satiri).
    2. `PROCRASTINATE_ENABLED=true` env degiskenini set edin.
    3. `python -m procrastinate_app.worker` ile bir worker sureci baslatin
       (bkz. worker.py - stub).
"""
from __future__ import annotations

from django.conf import settings


def get_procrastinate_app():
    """Procrastinate App nesnesini lazy-import ile olusturur (STUB).

    TODO (gercek implementasyon):
        import procrastinate
        app = procrastinate.App(connector=procrastinate.PsycopgConnector())
        return app
    """
    if not settings.PROCRASTINATE_ENABLED:
        raise RuntimeError(
            "Procrastinate devre disi (PROCRASTINATE_ENABLED=false). "
            "Aktif etmek icin .env dosyasinda PROCRASTINATE_ENABLED=true yapin "
            "ve `procrastinate` paketini kurun."
        )
    try:
        import procrastinate
    except ImportError as exc:
        raise ImportError(
            "procrastinate paketi kurulu degil. `pip install procrastinate` ile kurun."
        ) from exc

    app = procrastinate.App(connector=procrastinate.testing.InMemoryConnector())
    return app
