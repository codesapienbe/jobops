from __future__ import annotations

from typing import Optional
import requests


class GroqService:
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key or ""
        self.base = "https://api.groq.com/openai/v1"

    def test_connection(self, timeout: float = 3.0) -> bool:
        if not self.api_key:
            return False
        try:
            r = requests.get(f"{self.base}/models", headers={"Authorization": f"Bearer {self.api_key}"}, timeout=timeout)
            return r.ok
        except Exception:
            return False
