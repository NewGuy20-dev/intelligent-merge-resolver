import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from integrations.ui_capture import capture_ui_states

class TestUICaptureWrapper(unittest.TestCase):
	def test_handle_no_node(self):
		res = capture_ui_states('.', 'http://localhost:3000', ['/'])
		self.assertTrue(('error' in res) or ('results' in res))

if __name__ == '__main__':
	unittest.main()