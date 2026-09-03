from fractions import Fraction
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_spec.crap import (  # noqa: E402
    CrapInputError,
    calculate_crap,
    crap_gate_passes,
    render_canonical_decimal,
)


class CrapFormulaTests(unittest.TestCase):
    def test_full_coverage_equals_cyclomatic_complexity(self):
        self.assertEqual(calculate_crap(4, 4, 4), Fraction(4, 1))

    def test_half_coverage_uses_exact_fraction(self):
        self.assertEqual(calculate_crap(2, 1, 2), Fraction(5, 2))

    def test_zero_coverage_adds_squared_complexity(self):
        self.assertEqual(calculate_crap(3, 0, 7), Fraction(12, 1))

    def test_fraction_is_reduced(self):
        self.assertEqual(calculate_crap(4, 3, 4), Fraction(17, 4))

    def test_exact_eight_passes(self):
        self.assertTrue(crap_gate_passes(8, 1, 1))

    def test_value_above_eight_fails(self):
        self.assertFalse(crap_gate_passes(9, 1, 1))

    def test_boolean_is_not_an_integer_input(self):
        with self.assertRaisesRegex(CrapInputError, "cyclomaticComplexityNotInteger"):
            calculate_crap(True, 1, 1)

    def test_complexity_must_be_positive(self):
        with self.assertRaisesRegex(CrapInputError, "cyclomaticComplexityOutOfRange"):
            calculate_crap(0, 1, 1)

    def test_covered_units_must_be_nonnegative(self):
        with self.assertRaisesRegex(CrapInputError, "coveredUnitsOutOfRange"):
            calculate_crap(1, -1, 1)

    def test_total_units_must_be_positive(self):
        with self.assertRaisesRegex(CrapInputError, "totalUnitsOutOfRange"):
            calculate_crap(1, 0, 0)

    def test_covered_units_cannot_exceed_total_units(self):
        with self.assertRaisesRegex(CrapInputError, "coveredUnitsExceedTotalUnits"):
            calculate_crap(1, 2, 1)


class CanonicalDecimalTests(unittest.TestCase):
    def test_fraction_with_finite_decimal_removes_trailing_zeroes(self):
        self.assertEqual(render_canonical_decimal(Fraction(17, 4)), "4.25")

    def test_repeating_fraction_is_limited_to_twelve_places(self):
        self.assertEqual(render_canonical_decimal(Fraction(1, 3)), "0.333333333333")

    def test_half_even_keeps_even_last_digit(self):
        value = Fraction(246_913_578_025, 2_000_000_000_000)
        self.assertEqual(render_canonical_decimal(value), "0.123456789012")

    def test_half_even_increments_odd_last_digit(self):
        value = Fraction(246_913_578_027, 2_000_000_000_000)
        self.assertEqual(render_canonical_decimal(value), "0.123456789014")

    def test_rounding_can_carry_into_integer_part(self):
        value = Fraction(1_999_999_999_999, 2_000_000_000_000)
        self.assertEqual(render_canonical_decimal(value), "1")

    def test_negative_fraction_is_rejected(self):
        with self.assertRaisesRegex(CrapInputError, "fractionMustBeNonnegative"):
            render_canonical_decimal(Fraction(-1, 3))


if __name__ == "__main__":
    unittest.main()
