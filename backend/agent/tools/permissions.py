"""
Agent tool-level permissions (tool-duzeyinde RBAC).

Her agent tool'u, `@tool_permission(roles={...})` decorator'i ile hangi
rollerin (admin/analyst/viewer) bu tool'u cagirabilecegini beyan eder.
Bu bilgi fonksiyona `_tool_meta` attribute'u olarak eklenir ve
`agent/client.py` icindeki AgentRunner, bir tool'u cagirmadan once
`can_invoke_tool(user, tool_fn)` ile kontrol eder.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable

DEFAULT_ALLOWED_ROLES = frozenset({"admin", "analyst"})


def tool_permission(roles: Iterable[str] = DEFAULT_ALLOWED_ROLES):
    """Bir agent tool fonksiyonuna izinli rolleri etiketleyen decorator.

    Kullanim:
        @tool_permission(roles={"admin", "analyst"})
        def run_gnn_analysis(graph_id: str) -> dict:
            ...
    """
    allowed_roles = frozenset(roles)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._tool_meta = {
            "name": func.__name__,
            "allowed_roles": allowed_roles,
            "doc": (func.__doc__ or "").strip(),
        }
        return wrapper

    return decorator


def can_invoke_tool(user, tool_fn: Callable) -> bool:
    """Verilen kullanicinin, verilen tool fonksiyonunu cagirma yetkisi var mi?"""
    meta = getattr(tool_fn, "_tool_meta", None)
    if meta is None:
        # Meta yoksa (decorator uygulanmamissa) guvenli tarafta kal: reddet.
        return False
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    return getattr(user, "role", None) in meta["allowed_roles"]
