import unittest

from _pytest.assertion.compare_text import _diff_text


def identity_highlighter(source: str, *, lexer: str) -> str:
    return source


class AssertionDiffTests(unittest.TestCase):
    def test_long_common_suffix_is_skipped_when_prefix_differs(self) -> None:
        suffix = "z" * 50
        lines = list(_diff_text("x" + suffix, "y" + suffix, identity_highlighter))
        self.assertTrue(any("identical trailing" in line for line in lines))
        self.assertTrue(all(suffix not in line for line in lines))
