import tempfile
import unittest
from pathlib import Path

from _pytest.pathlib import samefile_nofollow


class SameFileTests(unittest.TestCase):
    def test_normal_files_compare_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.py"
            second = Path(directory) / "second.py"
            first.touch()
            second.touch()
            self.assertTrue(samefile_nofollow(first, first))
            self.assertFalse(samefile_nofollow(first, second))
