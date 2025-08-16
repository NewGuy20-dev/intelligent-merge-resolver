from __future__ import annotations
import typing as t
from ..integrations.gemini_client import GeminiClient

class ContextCompressor:
	def __init__(self) -> None:
		self.gemini = GeminiClient()

	def compress(self, texts: list[str], max_size: int) -> list[str]:
		joined = "\n\n".join(texts)
		if len(joined) <= max_size:
			return texts
		# Try Gemini summarization if possible
		prompt = f"Summarize the following code/context to under {max_size} characters while preserving key APIs and intent. Return raw text only.\n\n{joined[:max_size*2]}"
		resp = self.gemini.generate_json(prompt)
		best = None
		if isinstance(resp, dict) and 'raw' in resp and isinstance(resp['raw'], str):
			best = resp['raw']
		elif isinstance(resp, dict):
			best = str(resp)
		if best and len(best) <= max_size:
			return [best]
		# Fallback: truncate
		return [joined[:max_size]]