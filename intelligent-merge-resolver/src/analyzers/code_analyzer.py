from __future__ import annotations
import ast
import typing as t

class CodeAnalyzer:
	def summarize(self, code: str) -> t.Dict[str, t.Any]:
		result: t.Dict[str, t.Any] = {"functions": 0, "classes": 0}
		try:
			node = ast.parse(code)
			for n in ast.walk(node):
				if isinstance(n, ast.FunctionDef):
					result["functions"] += 1
				elif isinstance(n, ast.ClassDef):
					result["classes"] += 1
		except Exception:
			result["error"] = "parse_failed"
		return result