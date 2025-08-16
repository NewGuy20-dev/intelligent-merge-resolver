from __future__ import annotations
import os
import typing as t
from functools import lru_cache
from .context_selector import ContextSelector
from .vector_database import InMemoryVectorDB
from .context_compressor import ContextCompressor

class VectorDatabase:
	pass

class CodeDependencyGraph:
	def neighbors(self, file_path: str) -> list:
		return []

class SemanticCodeIndex:
	def search(self, text: str, k: int = 5) -> list:
		return []

class CodebaseContextManager:
	def __init__(self, repo_path: str) -> None:
		self.repo_path = os.path.abspath(repo_path)
		self.vector_db = InMemoryVectorDB()
		self.code_graph = CodeDependencyGraph()
		self.semantic_index = SemanticCodeIndex()
		self.selector = ContextSelector(self)
		self.compressor = ContextCompressor()

	def scan_repo_files(self, limit: int = 5000) -> list[str]:
		paths: list[str] = []
		for root, _dirs, files in os.walk(self.repo_path):
			if any(seg.startswith('.') for seg in os.path.relpath(root, self.repo_path).split(os.sep)):
				continue
			for fn in files:
				p = os.path.join(root, fn)
				if os.path.getsize(p) > 2 * 1024 * 1024:
					continue
				paths.append(p)
				if len(paths) >= limit:
					return paths
		return paths

	@lru_cache(maxsize=256)
	def cached_context(self, conflict_file: str, max_size: int) -> t.Tuple[t.Tuple[str, ...], t.Tuple[str, ...]]:
		candidates = self.selector.select_candidates(conflict_file)
		self.vector_db.add_files([p for p, _ in candidates])
		snippets: list[str] = []
		files: list[str] = []
		for path, _reason in candidates:
			try:
				with open(path, 'r', encoding='utf-8', errors='ignore') as f:
					snippets.append(f.read())
					files.append(path)
			except Exception:
				continue
		compressed = self.compressor.compress(snippets, max_size=max_size)
		return tuple(files), tuple(compressed)

	async def get_relevant_context(self, conflict_file: str, max_size: int = 50000) -> t.Dict[str, t.Any]:
		files, context = self.cached_context(conflict_file, max_size)
		return {"files": list(files), "context": list(context)}