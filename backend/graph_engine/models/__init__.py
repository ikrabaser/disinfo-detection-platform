"""
graph_engine.models paketi iki seyi bir arada barindirir:

1. `PropagationGraph` - Django ORM modeli. Bir haberin sosyal medyada
   nasil yayildigini (paylasim agini) temsil eden meta veriyi saklar.
2. GNN model siniflarinin stub'lari (bkz. gcn.py, gat.py, graphsage.py).
   Bunlar torch_geometric uzerine kurulu gercek model siniflarinin
   iskeletleridir; gercek egitim/inference bu projenin kapsami disindadir.

Not: Django'nun "models" konvansiyonu genelde tek bir models.py dosyasi
bekler, fakat bir "models" paketi de gecerlidir - Django sadece
`<app_label>.models` import edilebilir oldugu surece modelleri bulur.
"""
from django.db import models as django_models


class PropagationGraph(django_models.Model):
    """Bir haberin/iddianin sosyal medyada yayilim grafiginin meta verisi.

    Gercek graf yapisi (node/edge listesi) agir oldugu icin JSONField
    icinde saklanir; buyuk olcekte bu, ayri bir graph DB (ör. Neo4j) veya
    dosya depolama (ör. S3'te .graphml) ile degistirilebilir.
    """

    source_analysis_query = django_models.CharField(max_length=255, blank=True)
    node_count = django_models.PositiveIntegerField(default=0)
    edge_count = django_models.PositiveIntegerField(default=0)

    # [{"id": "...", "type": "user"|"post", "attrs": {...}}, ...]
    nodes = django_models.JSONField(default=list, blank=True)
    # [{"source": "...", "target": "...", "type": "shares"|"replies", "attrs": {...}}, ...]
    edges = django_models.JSONField(default=list, blank=True)

    created_at = django_models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"PropagationGraph#{self.pk} ({self.node_count} node, {self.edge_count} edge)"


# GNN model sinif stub'lari disari aciliyor, boylece
# `from graph_engine.models import GCNModel` gibi importlar calisir.
from graph_engine.models.gcn import GCNModel  # noqa: E402,F401
from graph_engine.models.gat import GATModel  # noqa: E402,F401
from graph_engine.models.graphsage import GraphSAGEModel  # noqa: E402,F401
