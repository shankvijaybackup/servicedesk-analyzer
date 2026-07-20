"""Provider boundary for optional local language models."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class AIUnavailableError(RuntimeError):
    """Raised when optional local AI is not configured or cannot respond."""


@runtime_checkable
class AIProvider(Protocol):
    """Minimal provider interface used by advisory AI services."""

    @property
    def name(self) -> str:
        ...

    def available(self) -> bool:
        """Return whether the local provider is ready without raising."""
        ...

    def generate_json(
        self,
        *,
        system: str,
        prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate one JSON object or raise AIUnavailableError."""
        ...
