import os
import sys
import unittest

# Ensure src is importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.merge_detector import extract_conflicts


class TestMergeDetector(unittest.TestCase):
	def test_extract_single_conflict(self):
		text = """line1
<<<<<<< HEAD
current change
=======
incoming change
>>>>>>> feature
line2
"""
		conflicts = extract_conflicts(text)
		self.assertEqual(len(conflicts), 1)
		self.assertIn("current change", conflicts[0].current)
		self.assertIn("incoming change", conflicts[0].incoming)

	def test_no_conflict(self):
		text = "no conflicts here"
		self.assertEqual(extract_conflicts(text), [])


if __name__ == '__main__':
	unittest.main()