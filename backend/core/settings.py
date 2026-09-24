"""
Django settings for the "dezenformasyon-tespit-platformu" (disinformation
detection platform) project.

Bu proje; sosyal medyada yayilan sahte haberleri, haber yayilim grafigi
(propagation graph) uzerinde GNN, metin uzerinde NLP ve kullanici davranisi
uzerinde bot tespiti kullanarak analiz eder. Bu dosya sadece iskelet
(skeleton) amaclidir; production degerleri .env / ortam degiskenlerinden
okunmalidir.
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Core / security
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "procrastinate.contrib.django",
    # django-prometheus: opsiyonel, metrics endpoint icin. Gercek kurulum
    # yapilmadan once requirements.txt'e eklenmelidir.
    # "django_prometheus",
    # local apps
    "accounts",
    "agent",
    "nlp_engine",
    "graph_engine",
    "analyses",
    "realtime",
    "external",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# ---------------------------------------------------------------------------
# Database - PostgreSQL (DATABASE_URL uzerinden). pgvector opsiyonel bir
# extension olarak notlandirilmistir (asagida).
# ---------------------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

try:
    if not DATABASE_URL:
        raise ImportError("DATABASE_URL bos - sqlite'a dusuyoruz")

    import dj_database_url

    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
except ImportError:
    # dj-database-url kurulu degilse (ornegin sadece "django check" calistiriliyorsa),
    # skeleton'in import edilebilir kalmasi icin sqlite'a dusuyoruz.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# pgvector NOTU (opsiyonel):
# Embedding vektorlerini (ör. haber metni embedding'i) Postgres'te saklamak
# icin `pgvector` extension'i ve `django-pgvector` (veya benzeri) paketi
# kullanilabilir. Ornek (calistirmak icin gerekli degil, sadece dokuman amacli):
#
# CREATE EXTENSION IF NOT EXISTS vector;
#
# from pgvector.django import VectorField
# class ArticleEmbedding(models.Model):
#     embedding = VectorField(dimensions=384)
#
# Bu proje iskeletinde VectorField KULLANILMAMAKTADIR; sadece not olarak
# birakilmistir. Gercek entegrasyon icin analyses/models.py dosyasina bakiniz.

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# I18N - Turkce dil yapisina uygunluk hedefi
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.authentication.CookieJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "user": "120/minute",
        "anon": "30/minute",
        # Ajan (LLM tool-calling) uclari daha maliyetli oldugu icin ayri limit:
        "agent": "20/minute",
    },
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ---------------------------------------------------------------------------
# JWT (httponly cookie akisi) - rest_framework_simplejwt
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

JWT_AUTH_COOKIE = "access_token"
JWT_AUTH_REFRESH_COOKIE = "refresh_token"
JWT_AUTH_COOKIE_SECURE = os.environ.get("JWT_COOKIE_SECURE", "false").lower() == "true"
JWT_AUTH_COOKIE_SAMESITE = "Lax"
JWT_AUTH_COOKIE_HTTPONLY = True

# ---------------------------------------------------------------------------
# CORS - frontend (Vite dev server) icin
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Redis - realtime / cache / procrastinate icin backing store
# ---------------------------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# ---------------------------------------------------------------------------
# Centrifugo - gercek zamanli (real-time) analiz ilerleme yayinlari icin
# ---------------------------------------------------------------------------
CENTRIFUGO_API_URL = os.environ.get("CENTRIFUGO_API_URL", "http://localhost:8000/api")
CENTRIFUGO_API_KEY = os.environ.get("CENTRIFUGO_API_KEY", "dev-centrifugo-api-key")
CENTRIFUGO_HMAC_SECRET = os.environ.get("CENTRIFUGO_HMAC_SECRET", "dev-centrifugo-hmac-secret")

# ---------------------------------------------------------------------------
# OpenAI Agents SDK / OpenAI API - agent app tarafindan kullanilir
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_AGENT_MODEL = os.environ.get("OPENAI_AGENT_MODEL", "gpt-4o-mini")

# ---------------------------------------------------------------------------
# X (Twitter) API - external app tarafindan kullanilir (STUB, gercek cagri yok)
# ---------------------------------------------------------------------------
X_API_BEARER_TOKEN = os.environ.get("X_API_BEARER_TOKEN", "")
X_API_BASE_URL = os.environ.get("X_API_BASE_URL", "https://api.x.com/2")

# ---------------------------------------------------------------------------
# Higgsfield - external app tarafindan kullanilir (STUB, gercek cagri yok).
# Analiz sonuclarini tanitim gorseli/videosuna donusturmek icin.
# ---------------------------------------------------------------------------
HIGGSFIELD_API_KEY = os.environ.get("HIGGSFIELD_API_KEY", "")
HIGGSFIELD_API_BASE_URL = os.environ.get("HIGGSFIELD_API_BASE_URL", "https://api.higgsfield.ai")

# ---------------------------------------------------------------------------
# Procrastinate (async task queue) - opsiyonel, agir bagimlilik kurulana kadar
# devre disi birakilabilir. bkz. backend/procrastinate_app/
# ---------------------------------------------------------------------------
PROCRASTINATE_ENABLED = os.environ.get(
    "PROCRASTINATE_ENABLED",
    "false",
).lower() == "true"

PROCRASTINATE_IMPORT_PATHS = [
    "procrastinate_app.tasks",
]

# ---------------------------------------------------------------------------
# Monitoring - Sentry / Prometheus / Grafana notlari
# ---------------------------------------------------------------------------
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
    except ImportError:
        # sentry-sdk kurulu degilse sessizce atla (skeleton importable kalsin).
        pass

# Prometheus metrics endpoint: django-prometheus kurulduktan sonra
# INSTALLED_APPS + MIDDLEWARE + urls.py icindeki ilgili satirlarin
# yorumdan cikarilmasi yeterlidir (bkz. yukaridaki yorum satirlari ve
# core/urls.py).
