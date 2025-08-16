from __future__ import annotations
import os
import typing as t

try:
	import cv2
except Exception:  # pragma: no cover
	cv2 = None

try:
	import pytesseract
except Exception:  # pragma: no cover
	pytesseract = None

class OCRAnalyzer:
	def __init__(self) -> None:
		self.available = cv2 is not None and pytesseract is not None

	def preprocess(self, image_path: str):
		if not cv2:
			return None
		img = cv2.imread(image_path)
		if img is None:
			return None
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
		return th

	def analyze(self, image_path: str) -> t.Dict[str, t.Any]:
		if not self.available:
			return {"error": "ocr_unavailable"}
		img = self.preprocess(image_path)
		if img is None:
			return {"error": "image_load_failed"}
		# pytesseract expects PIL or raw image; use temporary conversion via cv2 to file
		text = pytesseract.image_to_string(img)
		return {"text": text, "confidence": None}