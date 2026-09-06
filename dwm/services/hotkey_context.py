from __future__ import annotations


def context_allows_hotkeys(enabled: bool, allowed_hwnds: frozenset[int] | None, foreground: int) -> bool:
    """None means global; an empty allowlist must release every shortcut."""
    return enabled and (allowed_hwnds is None or foreground in allowed_hwnds)
