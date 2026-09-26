import unittest
from types import MappingProxyType

from _pytest.monkeypatch import MonkeyPatch


class MonkeyPatchFailureTests(unittest.TestCase):
    def test_failed_setitem_does_not_leave_stale_undo(self) -> None:
        mapping = MappingProxyType({"x": 1})
        patch = MonkeyPatch()
        with self.assertRaises(TypeError):
            patch.setitem(mapping, "x", 2)
        self.assertEqual(mapping["x"], 1)
        patch.undo()

    def test_successful_mutations_still_undo(self) -> None:
        mapping = {"x": 1, "y": 2}
        patch = MonkeyPatch()
        patch.setitem(mapping, "x", 99)
        patch.delitem(mapping, "y")
        patch.undo()
        self.assertEqual(mapping, {"x": 1, "y": 2})
