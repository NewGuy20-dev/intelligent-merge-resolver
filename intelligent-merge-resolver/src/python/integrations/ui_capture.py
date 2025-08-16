from __future__ import annotations
import os
import json
import shlex
import typing as t
import subprocess

BRIDGE_PATH = os.path.join(os.path.dirname(__file__), 'puppeteer_bridge.cjs')


def capture_ui_states(project_path: str, base_url: str, routes: list[str], out_dir: str = 'screenshots') -> t.Dict[str, t.Any]:
	args = {
		"projectPath": project_path,
		"baseUrl": base_url,
		"routes": routes,
		"outDir": out_dir,
	}
	cmd = ["node", BRIDGE_PATH, json.dumps(args)]
	try:
		cp = subprocess.run(cmd, cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		if cp.returncode != 0:
			return {"error": cp.stderr.strip() or cp.stdout.strip()}
		try:
			return json.loads(cp.stdout.strip() or '{}')
		except Exception:
			return {"raw": cp.stdout}
	except FileNotFoundError:
		return {"error": "node_not_found"}