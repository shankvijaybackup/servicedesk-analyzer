"""Local HTTP adapter for llama.cpp's OpenAI-compatible server."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

from .base import AIUnavailableError


class LlamaCppHTTPProvider:
    """Call a user-managed llama-server on the loopback interface only."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8080",
        *,
        model: str = "local-model",
        timeout_seconds: float = 30.0,
    ) -> None:
        endpoint = endpoint.rstrip("/")
        parsed = urlparse(endpoint)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Local AI endpoint must use HTTP on the loopback interface")
        self.endpoint = endpoint
        self.model = model
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return f"llama.cpp:{self.model}"

    def available(self) -> bool:
        try:
            request = urllib.request.Request(f"{self.endpoint}/health", method="GET")
            with urllib.request.urlopen(request, timeout=min(self.timeout_seconds, 2.0)) as response:
                return 200 <= response.status < 300
        except (OSError, urllib.error.URLError, TimeoutError):
            return False

    def generate_json(
        self,
        *,
        system: str,
        prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": 640,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "service_desk_advisory",
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        request = urllib.request.Request(
            f"{self.endpoint}/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = payload["choices"][0]["message"]["content"]
            result = json.loads(content) if isinstance(content, str) else content
            if not isinstance(result, dict):
                raise ValueError("response content is not a JSON object")
            return result
        except (OSError, TimeoutError, urllib.error.URLError, KeyError, IndexError,
                TypeError, ValueError, json.JSONDecodeError) as error:
            raise AIUnavailableError(f"Local AI provider unavailable: {error}") from error
