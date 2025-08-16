import os
import sys
import tempfile
import unittest

# Ensure src is importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.conflict_analyzer import ConflictAnalyzer


class TestConflictAnalyzer(unittest.TestCase):
	def test_analyze_conflict(self):
		content = """start
<<<<<<< HEAD
foo()
=======
bar()
>>>>>>> branch
end
"""
		with tempfile.TemporaryDirectory() as td:
			fp = os.path.join(td, 'file.py')
			with open(fp, 'w') as f:
				f.write(content)
			meta = ConflictAnalyzer().analyze_conflict(fp)
			self.assertEqual(meta.file_path, fp)
			self.assertEqual(meta.conflict_type, 'code')
			self.assertIn('snippets', meta.__dict__)
			self.assertEqual(len(meta.snippets), 1)


if __name__ == '__main__':
	unittest.main()