from __future__ import annotations
import os
import typing as t
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

	async def get_relevant_context(self, conflict_file: str, max_size: int = 50000) -> t.Dict[str, t.Any]:
		candidates = self.selector.select_candidates(conflict_file)
		# Index candidates into vector DB if not present
		self.vector_db.add_files([p for p, _ in candidates])
		snippets: list[str] = []
		for path, _reason in candidates:
			try:
				with open(path, 'r', encoding='utf-8', errors='ignore') as f:
					text = f.read()
					snippets.append(text)
			except Exception:
				continue
		compressed = self.compressor.compress(snippets, max_size=max_size)
		return {"files": [p for p, _ in candidates], "context": compressed}