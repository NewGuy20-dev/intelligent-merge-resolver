from __future__ import annotations
import os
import typing as t
from dataclasses import dataclass
from .merge_detector import extract_conflicts

@dataclass
class ConflictMetadata:
	file_path: str
	conflict_type: str
	complexity: str
	snippets: t.List[dict]


class ConflictAnalyzer:
	def analyze_conflict(self, file_path: str) -> ConflictMetadata:
		with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
			content = f.read()
		conflicts = extract_conflicts(content)
		conflict_type = self._classify_type(file_path)
		complexity = "low" if len(conflicts) <= 1 else ("medium" if len(conflicts) <= 3 else "high")
		snippets = [{"current": c.current, "incoming": c.incoming} for c in conflicts]
		return ConflictMetadata(file_path=file_path, conflict_type=conflict_type, complexity=complexity, snippets=snippets)

	def _classify_type(self, file_path: str) -> str:
		ext = os.path.splitext(file_path)[1].lower()
		if ext in {".js", ".jsx", ".ts", ".tsx"}:
			return "ui" if "component" in file_path.lower() else "code"
		if ext in {".json", ".yml", ".yaml"}:
			return "config"
		return "code"