from rest_framework import serializers

from analyses.models import Analysis


class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = [
            "id",
            "claim_text",
            "source_url",
            "query",
            "created_by",
            "status",
            "nlp_result",
            "gnn_result",
            "bot_analysis_result",
            "ai_analysis_result",
            "source_verification_result",
            "truth_score",
            "propagation_graph",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "status",
            "nlp_result",
            "gnn_result",
            "bot_analysis_result",
            "ai_analysis_result",
            "source_verification_result",
            "truth_score",
            "created_at",
            "updated_at",
        ]


class AnalysisCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = ["claim_text", "source_url", "query"]
