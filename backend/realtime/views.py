"""
Realtime app view'lari.

NOT: Gercek WebSocket baglantisi Django tarafindan degil, dogrudan
Centrifugo sunucusu tarafindan yonetilir (frontend, Centrifugo'nun
JS istemcisi ile dogrudan baglanir). Django tarafinda sadece:
  1. Centrifugo baglanti token'i uretilen bir endpoint (`/connect-token/`)
  2. (Opsiyonel) Server-Sent Events (SSE) fallback endpoint'i
gerekir. Asagida bu iki uc de STUB olarak taniml anmistir.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class CentrifugoConnectTokenView(APIView):
    """Frontend'in Centrifugo'ya baglanmak icin kullanacagi JWT token'i uretir.

    TODO: gercek implementasyonda `settings.CENTRIFUGO_HMAC_SECRET` ile
    imzalanmis bir JWT (Centrifugo'nun bekledigi formatta: {"sub": user_id})
    uretilmelidir (PyJWT kullanilarak).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # STUB - gercek JWT imzalama TODO.
        return Response({"token": "mock-centrifugo-connect-token", "user": request.user.username})


class AnalysisProgressSSEView(APIView):
    """Server-Sent Events (SSE) fallback endpoint - STUB.

    TODO: gercek implementasyonda `StreamingHttpResponse` ile Redis pub/sub
    kanalindan okunan event'ler `text/event-stream` formatinda akitilmalidir.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, analysis_id: int):
        return Response(
            {
                "detail": "SSE stub - gercek implementasyon icin StreamingHttpResponse kullanin.",
                "analysis_id": analysis_id,
            }
        )
