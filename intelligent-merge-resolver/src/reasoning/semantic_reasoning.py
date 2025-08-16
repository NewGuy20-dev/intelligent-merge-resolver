from __future__ import annotations
from ..integrations.gemini_client import GeminiClient

class SemanticReasoning:
	layer_name = "semantic"

	def __init__(self) -> None:
		self.gemini = GeminiClient()

	async def analyze(self, reasoning_context):
		prompt = f"""
		[LAYER] REASONING PHASE: SEMANTIC
		Previous Context: {reasoning_context.get_previous_reasoning()}
		Respond JSON with semantic_analysis, semantic_reasoning_chain, semantic_confidence.
		"""
		resp = self.gemini.generate_json(prompt)
		reasoning_context.add_reasoning_layer(self.layer_name, resp)
		return reasoning_context