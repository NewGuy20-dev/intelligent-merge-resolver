from __future__ import annotations
import typing as t
from ..integrations.gemini_client import GeminiClient

class ContextualReasoning:
	layer_name = "contextual"

	def __init__(self) -> None:
		self.gemini = GeminiClient()

	async def analyze(self, reasoning_context):
		prompt = f"""
		[LAYER] REASONING PHASE: CONTEXTUAL
		Previous Context: {reasoning_context.get_previous_reasoning()}
		Respond JSON with contextual_analysis, contextual_reasoning_chain, contextual_confidence.
		"""
		resp = self.gemini.generate_json(prompt)
		reasoning_context.add_reasoning_layer(self.layer_name, resp)
		return reasoning_context