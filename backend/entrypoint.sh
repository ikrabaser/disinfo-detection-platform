#!/bin/sh
# Gunicorn entrypoint - production benzeri calisma icin.
set -e

echo "ML model artifact'lari kontrol ediliyor..."
python scripts/provision_model_artifacts.py

echo "Migrasyonlar uygulaniyor..."
python manage.py migrate --noinput

echo "Statik dosyalar toplaniyor..."
python manage.py collectstatic --noinput

echo "Gunicorn baslatiliyor..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
