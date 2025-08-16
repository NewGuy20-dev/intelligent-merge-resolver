import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from analyzers.ocr_analyzer import OCRAnalyzer

class TestOCRAnalyzer(unittest.TestCase):
	def test_availability(self):
		ocr = OCRAnalyzer()
		# Should return error if OCR stack unavailable
		res = ocr.analyze('nonexistent.png')
		self.assertTrue('error' in res or 'text' in res)

if __name__ == '__main__':
	unittest.main()