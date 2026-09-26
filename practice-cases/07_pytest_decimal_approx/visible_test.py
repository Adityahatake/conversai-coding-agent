import unittest
from decimal import Decimal

from _pytest.python_api import approx


class DecimalApproxTests(unittest.TestCase):
    def test_finite_decimal_outside_float_range_uses_relative_tolerance(self) -> None:
        expected = Decimal("1e400")
        actual = Decimal("1.0000001e400")
        self.assertTrue(actual == approx(expected, rel=Decimal("1e-6")))
        self.assertFalse(Decimal("2e400") == approx(expected, rel=Decimal("1e-6")))

    def test_ordinary_float_behavior_is_preserved(self) -> None:
        self.assertTrue(1.0000001 == approx(1.0, rel=1e-6))
        self.assertFalse(2.0 == approx(1.0, rel=1e-6))
