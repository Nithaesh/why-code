"""Small JSON-on-disk cache for deterministic, repeatable LLM requests."""

import hashlib
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from whycode.llm.base import LLMResult

logger = logging.getLogger(__name__)


class DiskCache:
    """Store response records under hashes of all generation-relevant inputs."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def make_key(
        provider: str,
        model: str,
        prompt: str,
        system: str | None,
        temperature: float,
        response_schema: dict[str, Any] | None,
    ) -> str:
        """Hash a canonical representation so different requests don't collide."""
        payload = {
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "system": system,
            "temperature": temperature,
            "response_schema": response_schema,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get(self, key: str) -> LLMResult | None:
        """Return a cached response, or None when no valid record exists."""
        path = self.directory / f"{key}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return LLMResult(
                text=data["text"],
                prompt_tokens=data.get("prompt_tokens"),
                response_tokens=data.get("response_tokens"),
                latency_seconds=0.0,
                cache_hit=True,
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            # A corrupt cache should not prevent the user from making a fresh request.
            logger.warning("Ignoring invalid cache entry %s: %s", path.name, exc)
            return None

    def set(self, key: str, result: LLMResult) -> None:
        """Persist a response atomically to avoid half-written cache files."""
        path = self.directory / f"{key}.json"
        temporary_path = self.directory / f"{key}.tmp"
        data = asdict(result)
        data.pop("cache_hit", None)
        data.pop("latency_seconds", None)
        try:
            temporary_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            temporary_path.replace(path)
        except OSError:
            logger.exception("Could not write cache entry %s", path.name)
            raise
