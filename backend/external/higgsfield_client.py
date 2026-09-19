"""
Higgsfield API istemcisi - STUB.

ONEMLI: Bu modul GERCEK bir Higgsfield API cagrisi YAPMAZ. Bir analiz
sonucunu (dogruluk skoru, propagasyon grafigi ozeti vb.) paylasima hazir bir
tanitim gorseline/videosuna donusturmek icin kullanilacak istemcinin arayuzu
burada tanimlanmistir; gercek implementasyonda `requests` ile Higgsfield
REST API'sine (bkz. `settings.HIGGSFIELD_API_BASE_URL`) baglanilmalidir.

TODO (gercek implementasyon):
    import requests
    response = requests.post(
        f"{settings.HIGGSFIELD_API_BASE_URL}/v1/generate",
        headers={"Authorization": f"Bearer {settings.HIGGSFIELD_API_KEY}"},
        json={"prompt": prompt, "type": media_type},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
"""
from __future__ import annotations

from django.conf import settings


class MockHiggsfieldClient:
    """Higgsfield istemcisinin gercek olmayan (mock) implementasyonu."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_summary_image(self, analysis_id: str, prompt: str) -> dict:
        """Bir analiz sonucundan mock bir ozet gorseli uretim istegi doner.

        TODO: gercek implementasyonda Higgsfield'in goruntu uretim
        endpoint'ine `prompt` gonderilip uretilen medyanin URL/ID'si
        donmelidir.
        """
        return {
            "job_id": f"mock-higgsfield-image-{analysis_id}",
            "status": "queued",
            "media_type": "image",
            "prompt": prompt,
            "result_url": None,
        }

    def generate_summary_video(self, analysis_id: str, prompt: str) -> dict:
        """Bir analiz sonucundan mock bir ozet videosu uretim istegi doner.

        TODO: gercek implementasyonda Higgsfield'in video uretim
        endpoint'ine `prompt` gonderilip uretim isinin job_id'si donmeli,
        durumu `get_job_status` ile sorgulanmalidir.
        """
        return {
            "job_id": f"mock-higgsfield-video-{analysis_id}",
            "status": "queued",
            "media_type": "video",
            "prompt": prompt,
            "result_url": None,
        }

    def get_job_status(self, job_id: str) -> dict:
        """Mock uretim isi durumu doner.

        TODO: gercek implementasyonda ilgili job_id icin Higgsfield'den
        durum sorgulanmali (queued/processing/completed/failed) ve
        tamamlaninca `result_url` doldurulmalidir.
        """
        return {
            "job_id": job_id,
            "status": "completed",
            "result_url": f"https://mock-higgsfield.local/media/{job_id}.png",
        }


def get_higgsfield_client() -> MockHiggsfieldClient:
    """Higgsfield istemcisini env degiskenlerinden yapilandirip doner (STUB).

    `settings.HIGGSFIELD_API_KEY` bos ise bile mock istemci calismaya devam
    eder - boylece gelistirme ortaminda gercek API anahtari olmadan da
    sistem uctan uca test edilebilir.
    """
    api_key = settings.HIGGSFIELD_API_KEY
    # TODO: api_key bos degilse gercek requests tabanli istemci dondur.
    return MockHiggsfieldClient(api_key=api_key)
