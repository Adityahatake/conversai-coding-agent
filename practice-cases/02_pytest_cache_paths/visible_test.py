import tempfile
import unittest
from pathlib import Path

from _pytest.cacheprovider import Cache


class CachePathTests(unittest.TestCase):
    def test_value_keys_cannot_escape_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = Cache(root / ".pytest_cache", object(), _ispytest=True)
            with self.assertRaises(ValueError):
                cache.set("../escaped", {"secret": True})
            with self.assertRaises(ValueError):
                cache.get("plugin/../../escaped", None)
            self.assertFalse((root / "escaped").exists())

    def test_mkdir_rejects_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = Cache(Path(directory) / ".pytest_cache", object(), _ispytest=True)
            with self.assertRaises(ValueError):
                cache.mkdir("..")
