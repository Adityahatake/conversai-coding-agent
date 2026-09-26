import tempfile
import unittest
from pathlib import Path

from _pytest.config import UsageError
from _pytest.config.findpaths import load_config_dict_from_file


class TomlConfigTests(unittest.TestCase):
    def test_top_level_options_raise_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pytest.toml"
            path.write_text('minversion = "3.11"\naddopts = ["-v"]\n', encoding="utf-8")
            with self.assertRaises(UsageError) as caught:
                load_config_dict_from_file(path)
            message = str(caught.exception)
            self.assertIn("configuration must be under a [pytest] table", message)
            self.assertIn("minversion, addopts", message)

    def test_valid_pytest_table_is_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pytest.toml"
            path.write_text('[pytest]\naddopts = ["-q"]\n', encoding="utf-8")
            config = load_config_dict_from_file(path)
            self.assertEqual(config["addopts"].value, ["-q"])
