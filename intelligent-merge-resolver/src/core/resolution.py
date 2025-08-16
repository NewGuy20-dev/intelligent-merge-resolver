from __future__ import annotations
import re

START = re.compile(r"^<<<<<<< .*$", re.M)
SEP = re.compile(r"^=======\s*$", re.M)
END = re.compile(r"^>>>>>>> .*$", re.M)


def resolve_conflicts_in_text(text: str, choice: str = "current") -> str:
	"""
	choice: 'current' or 'incoming'
	"""
	lines = text.splitlines(keepends=True)
	out = []
	i = 0
	while i < len(lines):
		if lines[i].startswith("<<<<<<< "):
			i += 1
			cur = []
			while i < len(lines) and not SEP.match(lines[i]):
				cur.append(lines[i])
				i += 1
			i += 1  # skip sep
			inc = []
			while i < len(lines) and not lines[i].startswith(">>>>>>> "):
				inc.append(lines[i])
				i += 1
			i += 1  # skip end
			out.extend(cur if choice == "current" else inc)
		else:
			out.append(lines[i])
			i += 1
	return "".join(out)