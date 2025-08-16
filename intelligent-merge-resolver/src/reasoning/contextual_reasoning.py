from __future__ import annotations
import typing as t
from ..integrations.gemini_client import GeminiClient

class ContextualReasoning:
	layer_name = "contextual"

	def __init__(self, gemini_client: GeminiClient | None = None) -> None:
		self.gemini = gemini_client or GeminiClient()

	async def analyze(self, reasoning_context):
		prompt = f"""
		[LAYER] REASONING PHASE: CONTEXTUAL
		Previous Context: {reasoning_context.get_previous_reasoning()}
		ANALYSIS TASKS:
		1. Identify project context, change intentions, requirement alignment
		2. Provide step-by-step reasoning
		3. Output strictly in JSON fields below
		Respond with structured JSON:
		{{
		  "contextual_analysis": {{"summary": "...", "assumptions": [], "risks": []}},
		  "contextual_reasoning_chain": ["..."],
		  "contextual_confidence": 0.0
		}}
		"""
		resp = self.gemini.generate_json(prompt)
		reasoning_context.add_reasoning_layer(self.layer_name, resp)
		return reasoning_context