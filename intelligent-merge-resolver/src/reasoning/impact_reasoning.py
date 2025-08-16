from __future__ import annotations
from ..integrations.gemini_client import GeminiClient

class ImpactReasoning:
	layer_name = "impact"

	def __init__(self) -> None:
		self.gemini = GeminiClient()

	async def analyze(self, reasoning_context):
		prompt = f"""
		[LAYER] REASONING PHASE: IMPACT
		Previous Context: {reasoning_context.get_previous_reasoning()}
		Respond JSON with impact_analysis, impact_reasoning_chain, impact_confidence.
		"""
		resp = self.gemini.generate_json(prompt)
		reasoning_context.add_reasoning_layer(self.layer_name, resp)
		return reasoning_context