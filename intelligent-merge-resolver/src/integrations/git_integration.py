from __future__ import annotations
import subprocess
import typing as t
from dataclasses import dataclass

@dataclass
class Conflict:
	file_path: str
	status: str


class GitIntegration:
	def __init__(self, repo_path: str = ".") -> None:
		self.repo_path = repo_path

	def _run(self, *args: str) -> str:
		cp = subprocess.run(["git", *args], cwd=self.repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		if cp.returncode != 0:
			raise RuntimeError(cp.stderr.strip())
		return cp.stdout

	def install_hooks(self, repo_path: t.Optional[str] = None) -> None:
		# Placeholder: write hook files from hooks/ into .git/hooks/
		pass

	def detect_conflicts(self) -> t.List[Conflict]:
		out = self._run("status", "--porcelain")
		conflicts: t.List[Conflict] = []
		for line in out.splitlines():
			if line.startswith("UU ") or line.startswith("AA ") or line.startswith("DD "):
				path = line[3:]
				conflicts.append(Conflict(file_path=path, status=line[:2].strip()))
		return conflicts