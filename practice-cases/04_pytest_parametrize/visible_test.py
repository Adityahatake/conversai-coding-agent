import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def collect(source: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        test_file = Path(directory) / "test_example.py"
        test_file.write_text(source, encoding="utf-8")
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", str(test_file)],
            cwd=directory,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
        )


class ParametrizeTests(unittest.TestCase):
    def test_scalar_parameter_set_has_clear_collection_error(self) -> None:
        result = collect(
            'import pytest\n@pytest.mark.parametrize("x,", [None])\ndef test_func(x): pass\n'
        )
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected a sequence of values, got NoneType", output)
        self.assertIn("None", output)
        self.assertNotIn("object of type 'NoneType' has no len()", output)

    def test_valid_tuple_style_still_collects(self) -> None:
        result = collect(
            'import pytest\n@pytest.mark.parametrize("x,", [(1,), (2,)])\ndef test_func(x): pass\n'
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
