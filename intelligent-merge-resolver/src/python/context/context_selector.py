from __future__ import annotations
import os
import typing as t
import subprocess

class DirectDependencyStrategy:
	def select(self, conflict_file: str, manager: t.Any) -> list[tuple[str, str]]:
		neighbors = manager.code_graph.neighbors(conflict_file) or []
		return [(n, "direct_dependency") for n in neighbors]

class SemanticSimilarityStrategy:
	def select(self, conflict_file: str, manager: t.Any) -> list[tuple[str, str]]:
		# Use file content as query
		try:
			with open(conflict_file, 'r', encoding='utf-8', errors='ignore') as f:
				text = f.read()
		except Exception:
			text = os.path.basename(conflict_file)
		results = manager.vector_db.query(text, k=5)
		return [(r, "semantic_similarity") for r in results]

class ArchitecturalPatternStrategy:
	def select(self, conflict_file: str, manager: t.Any) -> list[tuple[str, str]]:
		candidates: list[str] = []
		base = os.path.basename(conflict_file)
		name, ext = os.path.splitext(base)
		for root, _, files in os.walk(manager.repo_path):
			for fn in files:
				if fn.startswith(name) and fn.endswith(ext):
					candidates.append(os.path.join(root, fn))
		return [(p, "architectural_pattern") for p in candidates[:5]]

class RecentChangesStrategy:
	def select(self, conflict_file: str, manager: t.Any) -> list[tuple[str, str]]:
		try:
			cp = subprocess.run(["git", "log", "-n", "50", "--name-only", "--pretty=format:"], cwd=manager.repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
			if cp.returncode != 0:
				return []
			files = [os.path.join(manager.repo_path, p) for p in set(filter(None, cp.stdout.splitlines()))]
			return [(p, "recent_change") for p in files if os.path.isfile(p)][:10]
		except Exception:
			return []

class ContextSelector:
	strategies = [
		DirectDependencyStrategy(),
		SemanticSimilarityStrategy(),
		ArchitecturalPatternStrategy(),
		RecentChangesStrategy(),
	]

	def __init__(self, manager: t.Any) -> None:
		self.manager = manager

	def select_candidates(self, conflict_file: str) -> list[tuple[str, str]]:
		seen: set[str] = set()
		candidates: list[tuple[str, str]] = []
		for strat in self.strategies:
			for path, reason in strat.select(conflict_file, self.manager):
				if path not in seen and os.path.isfile(path):
					seen.add(path)
					candidates.append((path, reason))
		return candidates