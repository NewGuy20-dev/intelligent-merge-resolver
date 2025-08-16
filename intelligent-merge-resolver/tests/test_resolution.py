import os
import sys
import tempfile
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.resolution import resolve_conflicts_in_text
from core.backup import BackupManager, DecisionLogger

class TestResolution(unittest.TestCase):
	def test_resolve_conflicts_current(self):
		text = """a
<<<<<<< HEAD
C
=======
I
>>>>>>> x
b
"""
		out = resolve_conflicts_in_text(text, choice='current')
		self.assertIn('C', out)
		self.assertNotIn('I', out)

	def test_backup_and_log(self):
		with tempfile.TemporaryDirectory() as td:
			p = os.path.join(td, 'f.txt')
			os.makedirs(os.path.join(td, '.imr'), exist_ok=True)
			with open(p, 'w') as f:
				f.write('hi')
			bm = BackupManager(td)
			b = bm.backup_file(p)
			self.assertTrue(os.path.isfile(b))
			dl = DecisionLogger(td)
			dl.log({"file": "f.txt", "choice": "current", "confidence": 0.9})
			self.assertTrue(os.path.isfile(os.path.join(td, '.imr', 'decisions.log.jsonl')))

if __name__ == '__main__':
	unittest.main()