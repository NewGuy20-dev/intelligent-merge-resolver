from __future__ import annotations
import os
import json
import time
import typing as t
from dataclasses import dataclass

try:
	import google.generativeai as genai
except Exception:  # pragma: no cover
	genai = None


@dataclass
class GeminiConfig:
	model: str = "gemini-2.0-flash-exp"
	max_tokens: int = 8192
	rate_limit_qps: float = 2.0


class GeminiClient:
	def __init__(self, api_key: t.Optional[str] = None, config: t.Optional[GeminiConfig] = None) -> None:
		self.api_key = api_key or os.getenv("GEMINI_API_KEY")
		self.config = config or GeminiConfig()
		self._last_call_ts = 0.0
		if genai and self.api_key:
			genai.configure(api_key=self.api_key)

	def _throttle(self) -> None:
		if self.config.rate_limit_qps <= 0:
			return
		min_interval = 1.0 / self.config.rate_limit_qps
		dt = time.time() - self._last_call_ts
		if dt < min_interval:
			time.sleep(min_interval - dt)
		self._last_call_ts = time.time()

	def generate_json(self, prompt: str, system_instruction: t.Optional[str] = None) -> t.Dict[str, t.Any]:
		"""
		Send a text prompt and expect a JSON-parsable response. Falls back to best-effort parsing.
		"""
		self._throttle()
		if not genai:
			return {"error": "google-generativeai not installed", "raw": None}
		if not self.api_key:
			return {"error": "GEMINI_API_KEY not configured", "raw": None}

		model = genai.GenerativeModel(self.config.model, system_instruction=system_instruction)
		resp = model.generate_content(prompt)
		text = getattr(resp, "text", None) or (resp.candidates[0].content.parts[0].text if getattr(resp, "candidates", None) else "")
		try:
			return json.loads(text)
		except Exception:
			return {"raw": text}

	def generate_multimodal_json(self, prompt: str, image_paths: list[str]) -> t.Dict[str, t.Any]:
		self._throttle()
		if not genai or not self.api_key:
			return {"error": "gemini_unavailable"}
		model = genai.GenerativeModel(self.config.model)
		parts: list[t.Any] = [prompt]
		for p in image_paths:
			try:
				parts.append({"mime_type": "image/png", "data": open(p, "rb").read()})
			except Exception:
				continue
		resp = model.generate_content(parts)
		text = getattr(resp, "text", None) or ""
		try:
			return json.loads(text)
		except Exception:
			return {"raw": text}