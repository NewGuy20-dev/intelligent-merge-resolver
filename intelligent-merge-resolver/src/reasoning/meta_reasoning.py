from __future__ import annotations
from ..integrations.gemini_client import GeminiClient

class MetaReasoning:
	layer_name = "meta"

	def __init__(self, gemini_client: GeminiClient | None = None) -> None:
		self.gemini = gemini_client or GeminiClient()

	async def analyze(self, reasoning_context):
		prompt = f"""
		[LAYER] REASONING PHASE: META
		Previous Context: {reasoning_context.get_previous_reasoning()}
		Respond JSON with keys: meta_analysis, meta_reasoning_chain, meta_confidence
		"""
		resp = self.gemini.generate_json(prompt)
		reasoning_context.add_reasoning_layer(self.layer_name, resp)
		return reasoning_context