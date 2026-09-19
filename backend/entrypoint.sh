#!/bin/sh
# Gunicorn entrypoint - production benzeri calisma icin.
set -e

echo "Migrasyonlar uygulaniyor..."
python manage.py migrate --noinput || echo "UYARI: migrate basarisiz oldu (DB henuz hazir olmayabilir)."

echo "Statik dosyalar toplaniyor..."
python manage.py collectstatic --noinput || echo "UYARI: collectstatic atlandi."

echo "Gunicorn baslatiliyor..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
