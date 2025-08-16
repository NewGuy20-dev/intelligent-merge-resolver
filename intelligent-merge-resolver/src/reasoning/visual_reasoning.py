from __future__ import annotations
from ..integrations.gemini_client import GeminiClient
from ..analyzers.ocr_analyzer import OCRAnalyzer

class VisualReasoning:
	layer_name = "visual"

	def __init__(self, gemini_client: GeminiClient | None = None) -> None:
		self.gemini = gemini_client or GeminiClient()
		self.ocr = OCRAnalyzer()

	async def analyze(self, reasoning_context):
		prompt = f"""
		[LAYER] REASONING PHASE: VISUAL
		Previous Context: {reasoning_context.get_previous_reasoning()}
		Respond JSON with keys: visual_analysis, visual_reasoning_chain, visual_confidence
		"""
		resp = self.gemini.generate_json(prompt)
		reasoning_context.add_reasoning_layer(self.layer_name, resp)
		return reasoning_context