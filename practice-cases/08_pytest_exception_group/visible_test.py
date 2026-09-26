import io
import unittest

from _pytest._code import ExceptionInfo
from _pytest._io import TerminalWriter


def render_current_exception() -> str:
    exception_info = ExceptionInfo.from_current()
    representation = exception_info.getrepr()
    output = io.StringIO()
    writer = TerminalWriter(file=output)
    writer.hasmarkup = False
    representation.toterminal(writer)
    return output.getvalue()


class ExceptionGroupTests(unittest.TestCase):
    def test_explicit_cause_is_rendered_once(self) -> None:
        try:
            try:
                raise RuntimeError("original cause")
            except RuntimeError as error:
                raise ExceptionGroup("group", [ValueError("inner")]) from error
        except ExceptionGroup:
            output = render_current_exception()

        self.assertEqual(output.count("RuntimeError: original cause"), 1)
        self.assertEqual(output.count("ExceptionGroup: group"), 1)
        self.assertEqual(output.count("ValueError: inner"), 1)
        self.assertEqual(output.count("The above exception was the direct cause"), 1)
