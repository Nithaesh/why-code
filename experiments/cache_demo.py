"""Tiny standalone experiment: see why identical requests can reuse a response."""

import hashlib
import json
import tempfile
from pathlib import Path


def cache_key(prompt: str) -> str:
    """Turn a prompt into a stable filename-like key."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


with tempfile.TemporaryDirectory() as folder:
    cache_file = Path(folder) / f"{cache_key('Explain a Git commit')}.json"
    print("First request: cache exists?", cache_file.exists())

    # Pretend this is the answer returned by an LLM API.
    cache_file.write_text(json.dumps({"text": "A commit records a repository change."}), encoding="utf-8")
    cached_response = json.loads(cache_file.read_text(encoding="utf-8"))

    print("Second identical request: reused response:", cached_response["text"])
    print("Different prompt gets a different key?", cache_key("Explain a Git commit") != cache_key("Explain a branch"))
