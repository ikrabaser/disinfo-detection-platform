"""Agent tool: run_bot_analysis."""
import hashlib

from agent.tools.permissions import tool_permission


@tool_permission(roles={"admin", "analyst"})
def run_bot_analysis(user_ids: list[str]) -> dict:
    """Verilen kullanici ID'leri icin bot-olma olasiligi skorlari uretir (mock).

    Args:
        user_ids: Bot analizi yapilacak sosyal medya kullanici ID'leri listesi.

    Returns:
        {
            "scores": {user_id: float, ...},  # 0 (kesin insan) - 1 (kesin bot)
            "flagged_users": list[str],        # skor > 0.7 olan kullanicilar
        }

    TODO: Gercek implementasyonda kullanici hesap yasi, paylasim sikligi,
    profil eksiklikleri, takipci/takip orani gibi ozellikler cikarilip
    egitilmis bir siniflandirici (ör. GNN veya klasik ML) ile skor
    uretilmelidir. Su an deterministik bir hash-tabanli MOCK kullanilir.
    """
    scores = {}
    for user_id in user_ids:
        digest = hashlib.sha256(user_id.encode("utf-8")).digest()
        # Deterministik, tekrarlanabilir mock skor (0.0 - 1.0 arasi).
        scores[user_id] = round((digest[0] / 255.0), 3)

    flagged = [uid for uid, score in scores.items() if score > 0.7]
    return {"scores": scores, "flagged_users": flagged}
