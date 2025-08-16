import os
import sys
import tempfile
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from cli.utils.config_loader import load_config

class TestConfigLoader(unittest.TestCase):
	def test_defaults(self):
		with tempfile.TemporaryDirectory() as td:
			cfg = load_config(td)
			self.assertIn('project', cfg)
			self.assertEqual(cfg['reasoning']['max_context_size'], 50000)

	def test_merge_user_config(self):
		with tempfile.TemporaryDirectory() as td:
			p = os.path.join(td, '.merge-resolver.yaml')
			with open(p, 'w') as f:
				f.write('project:\n  type: react\nreasoning:\n  max_context_size: 123\n')
			cfg = load_config(td)
			self.assertEqual(cfg['project']['type'], 'react')
			self.assertEqual(cfg['reasoning']['max_context_size'], 123)

if __name__ == '__main__':
	unittest.main()