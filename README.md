# Sosyal Medyada Dezenformasyon ve Sahte Haber Tespit Platformu

## Proje Amaci

Sosyal medya platformlarında yayılan sahte haberlerin ve manipülatif
içeriklerin tespiti için sadece metin analizine değil, haberin yayılım
grafiğine odaklanan bir model geliştirilecektir. Proje kapsamında, haberin
kimler tarafından paylaşıldığı, kullanıcılar arasındaki etkileşim ağları ve
yayılım hızı Graf Sinir Ağları (GNN) kullanılarak modellenecektir. Doğal Dil
İşleme (NLP) teknikleri ile metnin semantik analizi yapılırken, GNN ile de
haberin "bot" hesaplar tarafından organize bir şekilde yayılıp yayılmadığı
analiz edilecektir. Sistem, Türkçe dil yapısına uygun olarak eğitilecek ve
Twitter (X) gibi platformlardan canlı veri çekerek gerçek zamanlı bir
doğruluk skoru üretecektir.

Bu depo, yukarıdaki bitirme projesi fikrinin **iskeletini (skeleton)**
içerir: tüm klasör yapısı, ara yüzler (interface'ler) ve konfigürasyonlar
hedeflenen tam teknoloji yığınını yansıtacak şekilde kurulmuştur, ancak
ağır ML eğitimi ve gerçek X (Twitter) API çağrıları **kapsam dışıdır** ve
mock/stub veriyle değiştirilmiştir (kodda `TODO` olarak işaretlenmiştir).

## Teknoloji Yığını

**Frontend:** React + TypeScript + Vite + Tailwind CSS + Recharts (grafikler)
+ Cytoscape.js (yayılım ağı görselleştirmesi)

**Backend:** Python + Django + Django REST Framework + Django ORM

**Auth & Güvenlik:** Django auth, HttpOnly cookie üzerinden JWT
(`rest_framework_simplejwt`), basit RBAC (roller: `admin`, `analyst`,
`viewer`), DRF throttling, AI ajanı için tool-seviyesinde izin sistemi.

**AI Ajan Katmanı:** `agent` Django app'i, OpenAI Agents SDK / OpenAI API'yi
(`openai` paketi) tool-calling ile sarmalar. Tool'lar: `get_news`,
`get_social_posts`, `run_nlp_analysis`, `run_gnn_analysis`,
`run_bot_analysis`, `verify_sources`, `get_analysis_result`.

**NLP / ML:** `nlp_engine` app'i - PyTorch, Hugging Face Transformers,
Sentence Transformers, scikit-learn için stub arayüzler (`TextClassifier`,
`EmbeddingService`).

**Graph/GNN:** `graph_engine` app'i - PyTorch Geometric + NetworkX ile
yayılım grafiği inşası, GCN/GAT/GraphSAGE model iskeletleri
(`graph_engine/models/`).

**Veri İşleme:** `data_processing` - pandas/numpy tabanlı yardımcı modül.

**Veritabanı:** PostgreSQL (Django ORM, `DATABASE_URL`), opsiyonel
`pgvector` notu (`analyses/models.py` içinde yorum satırı olarak).

**Arka Plan İşleme:** Procrastinate (opsiyonel, `PROCRASTINATE_ENABLED`).

**Gerçek Zamanlı:** `realtime` app'i - Centrifugo entegrasyonu, Redis
backing store.

**Dış Veri:** `external` app'i - X API istemcisi (mock), haber kaynağı
fetcher (mock), Higgsfield istemcisi (mock) - analiz sonuçlarından
paylaşıma hazır özet görsel/video üretimi için.

**Altyapı:** Dockerfile (backend/frontend), `docker-compose.yml`,
`infra/nginx.conf`, gunicorn entrypoint.

**İzleme:** Sentry DSN notu, Prometheus metrics endpoint stub'u,
`grafana/` placeholder dashboard.

## Klasör Yapısı (özet)

```
backend/
  core/                # Django proje ayarları (settings, urls, wsgi, asgi)
  accounts/            # Auth + RBAC (custom User modeli, roller)
  agent/                # AI ajan katmanı (OpenAI wrapper + tools)
    tools/              # get_news, get_social_posts, run_nlp_analysis, ...
  nlp_engine/           # TextClassifier, EmbeddingService (stub)
  graph_engine/         # PropagationGraph modeli + GCN/GAT/GraphSAGE stub'ları
    models/
  data_processing/      # pandas/numpy yardımcıları (plain Python paketi)
  analyses/             # Analysis modeli (tüm sonuçları birleştiren ana model)
  realtime/             # Centrifugo client, SSE/WebSocket notları
  external/             # X API client (mock), haber fetcher (mock)
  procrastinate_app/    # Opsiyonel async task queue (stub)
  requirements.txt
  pytest.ini
frontend/
  src/
    api/client.ts       # HttpOnly cookie tabanlı axios client
    pages/               # Dashboard, AnalysisDetail, Login
    components/          # ScoreTrendChart (Recharts), PropagationGraph (Cytoscape)
infra/
  nginx.conf
grafana/
  dashboards/placeholder-dashboard.json
.github/workflows/ci.yml
docker-compose.yml
```

## Kurulum ve Çalıştırma

### Backend (Django)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # gerekirse degerleri duzenleyin
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

> Not: `DATABASE_URL` tanımlı değilse veya `dj-database-url`/`psycopg`
> kurulu değilse, ayarlar dosyası otomatik olarak SQLite'a düşer - böylece
> iskelet PostgreSQL kurulmadan da `python manage.py check` ile
> doğrulanabilir.

### Testler

```bash
cd backend
pytest
```

### Frontend (Vite + React)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Docker Compose (tüm sistem)

```bash
docker compose config   # yapılandırmayı doğrula
docker compose up --build
```

## Kasıtlı Olarak Eksik Bırakılanlar (TODO)

- **Gerçek GNN eğitimi/inference'i**: `graph_engine/models/*.py` içindeki
  `forward()` metodları mock sonuç döner; gerçek `torch_geometric` katmanları
  yazılmamıştır.
- **Gerçek NLP modeli**: `nlp_engine/text_classifier.py` ve
  `embedding_service.py` heuristic/hash tabanlı mock mantık kullanır;
  gerçek bir Türkçe fine-tune model (BERTurk vb.) entegre edilmemiştir.
- **Gerçek X (Twitter) API çağrıları**: `external/x_client.py` tamamen
  mock veri döner; gerçek `tweepy`/HTTP entegrasyonu yapılmamıştır.
- **Gerçek Higgsfield API çağrıları**: `external/higgsfield_client.py`
  tamamen mock veri döner; gerçek görsel/video üretim isteği
  gönderilmemiştir.
- **Gerçek OpenAI Agents SDK entegrasyonu**: `agent/client.py`,
  `OPENAI_API_KEY` boşken mock yanıt döner; gerçek tool-calling döngüsü
  (function calling loop) implemente edilmemiştir.
- **Procrastinate gerçek kurulumu**: `procrastinate_app/` stub'tır; gerçek
  worker süreci ve Postgres tabanlı kuyruk aktif değildir
  (`PROCRASTINATE_ENABLED=false`).
- **Centrifugo gerçek yayın**: `realtime/centrifugo_client.py` HTTP
  isteğini gerçekten atmaz, sadece loglar.
- **pgvector**: `analyses/models.py` içinde yorum satırı olarak bırakılmıştır,
  aktif değildir.
- **Prometheus/Sentry**: `django-prometheus` ve `sentry-sdk` paketleri
  `requirements.txt` içinde yorum satırıdır; gerçek kurulum yapılmamıştır.

## Rol Tabanlı Erişim (RBAC)

| Rol      | Yetkiler                                                  |
|----------|------------------------------------------------------------|
| admin    | Tüm işlemler (kullanıcı yönetimi dahil)                    |
| analyst  | Analiz oluşturma/çalıştırma, AI ajan tool'larının çoğu     |
| viewer   | Sadece salt-okunur görüntüleme                             |

Her AI ajan tool'u (`agent/tools/*.py`), `@tool_permission(roles={...})`
decorator'ı ile hangi rollerin onu çağırabileceğini beyan eder.
