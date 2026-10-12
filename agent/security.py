"""Input hardening helpers for untrusted event and ERP text."""

from __future__ import annotations

import re

_INJECTION_PATTERNS = (
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"system\s+prompt",
    r"developer\s+message",
    r"reveal\s+(the\s+)?(token|secret|credential|password)",
    r"authorization\s*:\s*bearer",
    r"execute\s+(this\s+)?command",
)


def sanitize_untrusted_text(value: str, *, max_length: int = 1000) -> tuple[str, bool]:
    """Remove control characters and quarantine likely prompt-injection text."""

    clean = "".join(char for char in value if char.isprintable() or char in "\n\t")
    clean = clean[:max_length]
    detected = any(re.search(pattern, clean, flags=re.IGNORECASE) for pattern in _INJECTION_PATTERNS)
    if detected:
        return "[Untrusted instruction removed from event text]", True
    return clean, False
