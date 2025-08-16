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

import urllib.request


@dataclass
class GeminiConfig:
	model: str = "gemini-2.0-flash-exp"
	max_tokens: int = 8192
	rate_limit_qps: float = 2.0


def _load_key_from_env_local() -> t.Optional[str]:
	"""
	Load GEMINI_API_KEY from a .env.local file in the current working directory.
	Simple KEY=VALUE parser with support for quoted values.
	"""
	path = os.path.join(os.getcwd(), ".env.local")
	if not os.path.isfile(path):
		return None
	try:
		with open(path, "r", encoding="utf-8", errors="ignore") as f:
			for raw in f:
				line = raw.strip()
				if not line or line.startswith("#"):
					continue
				if "=" not in line:
					continue
				key, value = line.split("=", 1)
				key = key.strip()
				val = value.strip().strip('"').strip("'")
				if key == "GEMINI_API_KEY" and val:
					return val
	except Exception:
		return None
	return None


def _detect_local_server(default_url: str = "http://127.0.0.1:3939") -> t.Optional[str]:
	try:
		with urllib.request.urlopen(default_url.rstrip("/") + "/status", timeout=0.3) as resp:
			if resp.status == 200:
				return default_url
	except Exception:
		pass
	return None


class GeminiClient:
	def __init__(self, api_key: t.Optional[str] = None, config: t.Optional[GeminiConfig] = None) -> None:
		# Priority: explicit arg -> env var -> .env.local
		env_key = os.getenv("GEMINI_API_KEY")
		file_key = _load_key_from_env_local()
		self.api_key = api_key or env_key or file_key
		self.config = config or GeminiConfig()
		self._last_call_ts = 0.0
		self.server_url = os.getenv("IMR_SERVER_URL") or _detect_local_server()
		if genai and self.api_key and not self.server_url:
			genai.configure(api_key=self.api_key)

	def _throttle(self) -> None:
		if self.config.rate_limit_qps <= 0:
			return
		min_interval = 1.0 / self.config.rate_limit_qps
		dt = time.time() - self._last_call_ts
		if dt < min_interval:
			time.sleep(min_interval - dt)
		self._last_call_ts = time.time()

	def _call_server(self, path: str, payload: dict) -> dict:
		if not self.server_url:
			raise RuntimeError("IMR_SERVER_URL not configured")
		url = self.server_url.rstrip("/") + path
		data = json.dumps(payload).encode("utf-8")
		req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
		with urllib.request.urlopen(req, timeout=60) as resp:
			text = resp.read().decode("utf-8")
			return json.loads(text)

	def generate_json(self, prompt: str, system_instruction: t.Optional[str] = None) -> t.Dict[str, t.Any]:
		"""
		Send a text prompt and expect a JSON-parsable response via local server when configured.
		"""
		self._throttle()
		if self.server_url:
			try:
				return self._call_server("/ai/generate-json", {"prompt": prompt, "system_instruction": system_instruction})
			except Exception as e:
				return {"error": f"server_error: {e}"}
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
		if self.server_url:
			# For brevity, route to text endpoint with prompt only
			try:
				return self._call_server("/ai/generate-json", {"prompt": prompt})
			except Exception as e:
				return {"error": f"server_error: {e}"}
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