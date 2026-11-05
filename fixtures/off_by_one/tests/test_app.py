import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import app


class AddTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(app.add(2, 2), 4)
