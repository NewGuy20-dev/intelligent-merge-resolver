from __future__ import annotations
import re
import typing as t

CONFLICT_START = re.compile(r"^<<<<<<< ")
CONFLICT_SEP = re.compile(r"^=======\s*$")
CONFLICT_END = re.compile(r"^>>>>>>> ")

class MergeConflict:
	def __init__(self, base: str, current: str, incoming: str) -> None:
		self.base = base
		self.current = current
		self.incoming = incoming


def extract_conflicts(text: str) -> t.List[MergeConflict]:
	lines = text.splitlines()
	conflicts: t.List[MergeConflict] = []
	i = 0
	while i < len(lines):
		if CONFLICT_START.match(lines[i] or ""):
			i += 1
			current_lines = []
			while i < len(lines) and not CONFLICT_SEP.match(lines[i] or ""):
				current_lines.append(lines[i])
				i += 1
			# skip sep
			i += 1
			incoming_lines = []
			while i < len(lines) and not CONFLICT_END.match(lines[i] or ""):
				incoming_lines.append(lines[i])
				i += 1
			# skip end
			i += 1
			conflicts.append(MergeConflict(base="", current="\n".join(current_lines), incoming="\n".join(incoming_lines)))
		else:
			i += 1
	return conflicts