from fractions import Fraction
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_spec.crap import crap_gate_passes  # noqa: E402
from sentinel_spec.mutation import MUTATION_STATES, evaluate_mutation  # noqa: E402
from sentinel_spec.threshold import (  # noqa: E402
    DEFAULT_CRAP_MAX,
    DEFAULT_MUTATION_MIN,
    ThresholdInputError,
    parse_crap_max,
    parse_mutation_min,
    parse_threshold,
)


def counts(**overrides):
    result = {state: 0 for state in MUTATION_STATES}
    result.update(overrides)
    return result


class ThresholdParsingTests(unittest.TestCase):
    def test_defaults_are_ninety_percent_and_crap_eight(self):
        self.assertEqual(("8", "90"), (DEFAULT_CRAP_MAX, DEFAULT_MUTATION_MIN))
        self.assertEqual(Fraction(8), parse_crap_max(DEFAULT_CRAP_MAX))
        self.assertEqual(Fraction(90), parse_mutation_min(DEFAULT_MUTATION_MIN))

    def test_decimal_text_is_read_exactly_without_binary_float(self):
        self.assertEqual(Fraction(17, 2), parse_threshold("8.5", "crapMax"))
        self.assertEqual(Fraction(1, 10), parse_threshold("0.1", "crapMax"))
        self.assertEqual(Fraction(7501, 100), parse_threshold("75.01", "mutationMin"))

    def test_rejects_non_text_and_malformed_thresholds(self):
        for value in (8, 8.0, None, True, "", "8.", ".5", "08", "8.000", "-1", "1e1", " 8", "abc"):
            with self.subTest(value=value):
                with self.assertRaises(ThresholdInputError) as raised:
                    parse_threshold(value, "crapMax")
                self.assertEqual("crapMaxInvalid", raised.exception.code)

    def test_range_limits_use_stable_codes(self):
        with self.assertRaises(ThresholdInputError) as raised:
            parse_crap_max("0")
        self.assertEqual("crapMaxOutOfRange", raised.exception.code)
        with self.assertRaises(ThresholdInputError) as raised:
            parse_mutation_min("100.01")
        self.assertEqual("mutationMinOutOfRange", raised.exception.code)
        self.assertEqual(Fraction(0), parse_mutation_min("0"))
        self.assertEqual(Fraction(1, 100), parse_crap_max("0.01"))


class ThresholdGateTests(unittest.TestCase):
    def test_crap_max_is_an_exact_comparison(self):
        self.assertTrue(crap_gate_passes(4, 3, 4, "4.25"))
        self.assertFalse(crap_gate_passes(4, 3, 4, "4.24"))
        self.assertTrue(crap_gate_passes(9, 1, 1, "9"))
        self.assertFalse(crap_gate_passes(9, 1, 1))

    def test_hundred_percent_minimum_equals_killed_only_gate(self):
        for state in MUTATION_STATES[1:]:
            with self.subTest(state=state):
                result = evaluate_mutation(counts(killed=3, **{state: 1}), 4, 0, "100")
                self.assertFalse(result.passed)
        self.assertTrue(evaluate_mutation(counts(killed=4), 4, 0, "100").passed)

    def test_lower_minimum_admits_a_kill_rate_at_or_above_it(self):
        partial = counts(killed=3, survived=1)
        self.assertTrue(evaluate_mutation(partial, 4, 0, "75").passed)
        self.assertFalse(evaluate_mutation(partial, 4, 0, "75.01").passed)
        self.assertEqual(Fraction(3, 4), evaluate_mutation(partial, 4, 0, "75").kill_rate)

    def test_zero_mutants_and_unauthorized_exclusion_never_pass(self):
        self.assertFalse(evaluate_mutation(counts(), 0, 0, "0").passed)
        self.assertFalse(evaluate_mutation(counts(killed=2), 2, 1, "0").passed)


if __name__ == "__main__":
    unittest.main()
