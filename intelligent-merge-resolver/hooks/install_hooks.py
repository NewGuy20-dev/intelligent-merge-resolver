from __future__ import annotations
import os
import shutil

def install(repo_path: str) -> None:
	hooks_src = os.path.dirname(__file__)
	hooks_dest = os.path.join(repo_path, ".git", "hooks")
	os.makedirs(hooks_dest, exist_ok=True)
	for name in ("pre-merge-commit", "post-merge"):
		src = os.path.join(hooks_src, name)
		dst = os.path.join(hooks_dest, name)
		if os.path.isfile(src):
			shutil.copyfile(src, dst)
			os.chmod(dst, 0o755)