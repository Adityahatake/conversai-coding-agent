import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def run_doctests(source: str, ini: str = "ELLIPSIS") -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        (path / "pytest.ini").write_text(
            f"[pytest]\ndoctest_optionflags = {ini}\n", encoding="utf-8"
        )
        (path / "example.py").write_text(source, encoding="utf-8")
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "pytest", "--doctest-modules", "-q", "example.py"],
            cwd=path,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
        )


class DoctestFlagTests(unittest.TestCase):
    def test_failed_docstring_does_not_disable_flag_for_next_docstring(self) -> None:
        result = run_doctests(
            '''def first():
    """
    >>> 0  # doctest: -ELLIPSIS
    2
    """

def second():
    """
    >>> print("foobar")
    foo...
    """
'''
        )
        output = result.stdout + result.stderr
        self.assertIn("1 failed, 1 passed", output)
