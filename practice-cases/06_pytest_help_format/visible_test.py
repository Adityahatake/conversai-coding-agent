import unittest

from _pytest.config import argparsing


class HelpFormattingTests(unittest.TestCase):
    def test_wraps_explicit_lines_separately(self) -> None:
        self.assertEqual(
            argparsing._split_help_text("one two three\nfour five", 8),
            ["one two", "three", "four", "five"],
        )

    def test_preserves_blank_lines(self) -> None:
        self.assertEqual(
            argparsing._split_help_text("first\n\nsecond", 40),
            ["first", "", "second"],
        )

    def test_dedents_docstring_style_help(self) -> None:
        help_text = """
            Select tests by marker expression.

            Examples:
                -m 'slow'
        """
        self.assertEqual(
            argparsing._split_help_text(help_text, 40),
            ["Select tests by marker expression.", "", "Examples:", "    -m 'slow'"],
        )
