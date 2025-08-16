from __future__ import annotations
import os
import json
import time
import typing as t

class BackupManager:
	def __init__(self, repo_path: str) -> None:
		self.repo_path = repo_path
		self.backup_dir = os.path.join(repo_path, ".imr", "backups")
		os.makedirs(self.backup_dir, exist_ok=True)

	def backup_file(self, file_path: str) -> str:
		base = os.path.relpath(file_path, self.repo_path).replace(os.sep, "__")
		stamp = time.strftime("%Y%m%d-%H%M%S")
		dst = os.path.join(self.backup_dir, f"{base}.{stamp}.bak")
		with open(file_path, 'rb') as rf, open(dst, 'wb') as wf:
			wf.write(rf.read())
		return dst

class DecisionLogger:
	def __init__(self, repo_path: str) -> None:
		self.log_path = os.path.join(repo_path, ".imr", "decisions.log.jsonl")
		os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

	def log(self, record: t.Dict[str, t.Any]) -> None:
		record = dict(record)
		record.setdefault("ts", time.time())
		with open(self.log_path, 'a', encoding='utf-8') as f:
			f.write(json.dumps(record) + "\n")