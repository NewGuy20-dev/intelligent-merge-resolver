from __future__ import annotations
import os
import json
import typing as t

from ..integrations.gemini_client import GeminiClient
from ..analyzers.ocr_analyzer import OCRAnalyzer
from ..analyzers.ui_comparator import compare_images

try:
	from ..integrations.js_bridge import JavaScriptBridge
except Exception:  # pragma: no cover
	JavaScriptBridge = None  # type: ignore

try:
	import yaml  # type: ignore
except Exception:  # pragma: no cover
	yaml = None  # type: ignore

class VisualReasoning:
	layer_name = "visual"

	def __init__(self, gemini_client: GeminiClient | None = None) -> None:
		self.gemini = gemini_client or GeminiClient()
		self.ocr = OCRAnalyzer()
		self.js = JavaScriptBridge() if JavaScriptBridge else None

	def _load_routes(self) -> list[str]:
		cfg_path = os.path.join(os.getcwd(), '.merge-resolver.yaml')
		if yaml and os.path.isfile(cfg_path):
			try:
				with open(cfg_path, 'r', encoding='utf-8') as f:
					cfg = yaml.safe_load(f) or {}
					return list(cfg.get('build', {}).get('test_routes', ['/']))
			except Exception:
				return ['/']
		return ['/']

	def _alignment_from_prefs(self, ocr_texts: list[str]) -> float:
		# Simple heuristic: if accessibility=high and OCR has text, boost score
		cfg_path = os.path.join(os.getcwd(), '.merge-resolver.yaml')
		acc = 'medium'
		if yaml and os.path.isfile(cfg_path):
			try:
				with open(cfg_path, 'r', encoding='utf-8') as f:
					cfg = yaml.safe_load(f) or {}
					acc = str(cfg.get('preferences', {}).get('accessibility', 'medium')).lower()
			except Exception:
				pass
		text_present = sum(1 for t in ocr_texts if t and t.strip())
		base = 0.5
		if acc == 'high' and text_present:
			base += 0.3
		return min(1.0, base)

	async def analyze(self, reasoning_context):
		# Capture screenshots using JS bridge when available
		routes = self._load_routes()
		out_dir = os.path.join('.imr', 'screenshots')
		os.makedirs(out_dir, exist_ok=True)
		screens = {}
		if self.js:
			try:
				result = self.js.capture_screenshots(routes, {'output_dir': out_dir})
				if isinstance(result, dict):
					screens = result
			except Exception:
				pass
		# OCR analysis
		ocr_results: dict[str, dict] = {}
		ocr_texts: list[str] = []
		for route, files in (screens or {}).items():
			for key in ('desktop', 'mobile'):
				fp = files.get(key)
				if not fp:
					continue
				res = self.ocr.analyze(fp)
				ocr_results[fp] = res
				if isinstance(res, dict) and 'text' in res and isinstance(res['text'], str):
					ocr_texts.append(res['text'])
		# UI comparison (desktop vs mobile) SSIM if both available
		ssim_scores: list[float] = []
		for route, files in (screens or {}).items():
			desktop = files.get('desktop')
			mobile = files.get('mobile')
			if desktop and mobile:
				comp = compare_images(desktop, mobile)
				if isinstance(comp, dict) and 'ssim' in comp:
					ssim_scores.append(float(comp['ssim']))
		# Aggregate visual metrics
		avg_ssim = sum(ssim_scores) / len(ssim_scores) if ssim_scores else None
		alignment = self._alignment_from_prefs(ocr_texts)
		visual_conf = 0.6 if ocr_texts else 0.4
		analysis = {
			"routes": routes,
			"screens": screens,
			"ocr_summary_count": len(ocr_texts),
			"avg_ssim": avg_ssim,
			"alignment_score": alignment,
		}
		# Optionally ask Gemini to summarize
		prompt = f"""
		Summarize the following visual analysis objectively and return JSON with fields: summary, risks.
		Analysis: {json.dumps(analysis)[:4000]}
		"""
		gem = self.gemini.generate_json(prompt)
		payload = {
			"visual_analysis": {"local": analysis, "ai": gem},
			"visual_reasoning_chain": ["captured_screenshots", "ran_ocr", "computed_ssim", "computed_alignment"],
			"visual_confidence": visual_conf,
		}
		reasoning_context.add_reasoning_layer(self.layer_name, payload)
		return reasoning_context