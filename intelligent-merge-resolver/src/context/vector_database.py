from __future__ import annotations
import os
import math
import typing as t
from collections import Counter, defaultdict

Token = str

class InMemoryVectorDB:
	def __init__(self) -> None:
		self.doc_id_to_tokens: dict[str, Counter[Token]] = {}
		self.token_to_df: Counter[Token] = Counter()

	def _tokenize(self, text: str) -> list[Token]:
		return [tok.lower() for tok in (text.replace('\n', ' ').replace('\t', ' ')).split() if tok]

	def add_document(self, doc_id: str, text: str) -> None:
		tokens = Counter(self._tokenize(text))
		self.doc_id_to_tokens[doc_id] = tokens
		for tkn in tokens.keys():
			self.token_to_df[tkn] += 1

	def add_files(self, paths: list[str]) -> None:
		for p in paths:
			try:
				with open(p, 'r', encoding='utf-8', errors='ignore') as f:
					self.add_document(p, f.read())
			except Exception:
				continue

	def _cosine(self, a: Counter[Token], b: Counter[Token]) -> float:
		# tf-idf weighting (idf = 1/df)
		common = set(a.keys()) | set(b.keys())
		wa = {}
		wb = {}
		for tkn in common:
			idf = 1.0 / float(self.token_to_df.get(tkn, 1))
			wa[tkn] = a.get(tkn, 0.0) * idf
			wb[tkn] = b.get(tkn, 0.0) * idf
		num = sum(wa[t]*wb[t] for t in common)
		da = math.sqrt(sum(v*v for v in wa.values()))
		db = math.sqrt(sum(v*v for v in wb.values()))
		if da == 0 or db == 0:
			return 0.0
		return num / (da * db)

	def query(self, text: str, k: int = 5) -> list[str]:
		q = Counter(self._tokenize(text))
		scores: list[tuple[str, float]] = []
		for doc_id, tokens in self.doc_id_to_tokens.items():
			s = self._cosine(q, tokens)
			scores.append((doc_id, s))
		scores.sort(key=lambda x: x[1], reverse=True)
		return [doc for doc, _ in scores[:k]]