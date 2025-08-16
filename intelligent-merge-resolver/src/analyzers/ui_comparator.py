from __future__ import annotations
import os
import typing as t

try:
	import cv2
	import numpy as np
	from skimage.metrics import structural_similarity as ssim  # type: ignore
except Exception:  # pragma: no cover
	cv2 = None
	ssim = None

def compare_images(img_path_a: str, img_path_b: str) -> t.Dict[str, t.Any]:
	if not cv2 or not ssim:
		return {"error": "ssim_unavailable"}
	imgA = cv2.imread(img_path_a)
	imgB = cv2.imread(img_path_b)
	if imgA is None or imgB is None:
		return {"error": "load_failed"}
	imgA = cv2.cvtColor(imgA, cv2.COLOR_BGR2GRAY)
	imgB = cv2.cvtColor(imgB, cv2.COLOR_BGR2GRAY)
	score, _ = ssim(imgA, imgB, full=True)
	return {"ssim": float(score)}