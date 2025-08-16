import os
import sys
import unittest

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), .., .., src))

from python.integrations.gemini_client import GeminiClient  # type: ignore

class TestGeminiEnvLocal(unittest.TestCase):
    def test_key_loaded_from_env_local(self):
        # Ensure env var is not set so .env.local is used
        os.environ.pop(GEMINI_API_KEY, None)
        # Read expected key from .env.local without hardcoding it
        expected = None
        with open(os.path.join(os.getcwd(), .env.local), r) as f:
            for line in f:
                if line.startswith(GEMINI_API_KEY=):
                    expected = line.strip().split(=, 1)[1].strip().strip(').strip(")
                    break
        self.assertIsNotNone(expected)
        client = GeminiClient()
        self.assertEqual(client.api_key, expected)

if __name__ == __main__:
    unittest.main()
