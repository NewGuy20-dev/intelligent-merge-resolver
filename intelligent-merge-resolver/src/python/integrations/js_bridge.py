from __future__ import annotations
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any

class JavaScriptBridge:
	"""Bridge for communicating with JavaScript utilities"""

	def __init__(self) -> None:
		self.js_dir = Path(__file__).parent.parent.parent / 'js'
		self.node_cmd = self._find_node()

	def _find_node(self) -> str:
		for cmd in ('node', 'nodejs'):
			try:
				subprocess.run([cmd, '--version'], capture_output=True, check=True)
				return cmd
			except Exception:
				continue
		raise RuntimeError('Node.js not found')

	def detect_project_type(self) -> str:
		script = self.js_dir / 'utils' / 'project-detector.js'
		cp = subprocess.run([self.node_cmd, str(script), '--cwd', os.getcwd()], capture_output=True, text=True)
		if cp.returncode == 0:
			return (cp.stdout or 'generic').strip()
		return 'generic'

	def capture_screenshots(self, routes: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
		script = self.js_dir / 'puppeteer' / 'screenshot.js'
		payload = json.dumps({
			'routes': routes,
			'output_dir': config.get('output_dir', 'screenshots'),
		})
		cp = subprocess.run([self.node_cmd, str(script)], input=payload, text=True, capture_output=True)
		if cp.returncode == 0:
			try:
				return json.loads(cp.stdout or '{}')
			except Exception:
				return {'raw': cp.stdout}
		return {'error': cp.stderr or 'capture_failed'}