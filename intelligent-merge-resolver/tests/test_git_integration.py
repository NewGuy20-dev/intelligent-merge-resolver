import os
import sys
import subprocess
import tempfile
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from integrations.git_integration import GitIntegration


def _run(cwd, *args):
	cp = subprocess.run(["git", *args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
	if cp.returncode != 0:
		raise RuntimeError(cp.stderr)
	return cp.stdout

class TestGitIntegration(unittest.TestCase):
	def test_detect_conflicts(self):
		with tempfile.TemporaryDirectory() as td:
			_run(td, 'init')
			# Configure identity
			_run(td, 'config', 'user.email', 't@example.com')
			_run(td, 'config', 'user.name', 'Test')
			# Create base commit
			with open(os.path.join(td, 'f.txt'), 'w') as f:
				f.write('hello\n')
			_run(td, 'add', 'f.txt')
			_run(td, 'commit', '-m', 'base')
			# Branch and diverge
			_run(td, 'checkout', '-b', 'feat')
			with open(os.path.join(td, 'f.txt'), 'w') as f:
				f.write('hello from feat\n')
			_run(td, 'commit', '-am', 'feat change')
			_run(td, 'checkout', '-')
			with open(os.path.join(td, 'f.txt'), 'w') as f:
				f.write('hello from main\n')
			_run(td, 'commit', '-am', 'main change')
			# Cause conflict
			# Merge feat into current, expect conflict state
			try:
				_run(td, 'merge', 'feat')
			except RuntimeError:
				pass
			gi = GitIntegration(td)
			conflicts = gi.detect_conflicts()
			self.assertTrue(any(c.file_path == 'f.txt' for c in conflicts))

if __name__ == '__main__':
	unittest.main()