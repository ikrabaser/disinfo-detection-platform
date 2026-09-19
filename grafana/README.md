# Grafana (placeholder)

Bu klasor, ileride Prometheus + django-prometheus entegrasyonu tamamlandiginda
kullanilacak Grafana dashboard tanimlarini icerir.

- `dashboards/placeholder-dashboard.json`: TODO panelleri iceren yer tutucu
  dashboard JSON'u. Gercek metrikler eklendiginde bu dosya guncellenmelidir.

Gercek kurulum icin (opsiyonel, docker-compose.yml icinde `grafana` servisi
yorum satiri olarak birakilmistir):

```yaml
grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  volumes:
    - ./grafana/dashboards:/var/lib/grafana/dashboards
```
