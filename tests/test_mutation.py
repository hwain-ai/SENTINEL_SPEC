from fractions import Fraction
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_spec.mutation import (  # noqa: E402
    MUTATION_STATES,
    MutationInputError,
    evaluate_mutation,
)


def counts(**overrides):
    result = {state: 0 for state in MUTATION_STATES}
    result.update(overrides)
    return result


class MutationGateTests(unittest.TestCase):
    def test_state_vocabulary_is_exact(self):
        self.assertEqual(
            MUTATION_STATES,
            (
                "killed",
                "survived",
                "uncovered",
                "timedOut",
                "compileError",
                "runtimeError",
                "pending",
                "ignored",
                "toolError",
            ),
        )

    def test_all_in_scope_mutants_killed_passes(self):
        result = evaluate_mutation(counts(killed=3), in_scope=3)
        self.assertTrue(result.passed)
        self.assertEqual(result.kill_rate, Fraction(1, 1))

    def test_surviving_mutant_fails_with_exact_kill_rate(self):
        result = evaluate_mutation(counts(killed=1, survived=1), in_scope=2)
        self.assertFalse(result.passed)
        self.assertEqual(result.kill_rate, Fraction(1, 2))

    def test_zero_mutants_fails_without_fabricated_kill_rate(self):
        result = evaluate_mutation(counts(), in_scope=0)
        self.assertFalse(result.passed)
        self.assertIsNone(result.kill_rate)

    def test_timeout_only_fails(self):
        result = evaluate_mutation(counts(timedOut=1), in_scope=1)
        self.assertFalse(result.passed)
        self.assertEqual(result.kill_rate, Fraction(0, 1))

    def test_ignored_only_fails(self):
        result = evaluate_mutation(counts(ignored=1), in_scope=1)
        self.assertFalse(result.passed)

    def test_unauthorized_exclusion_fails(self):
        result = evaluate_mutation(
            counts(killed=1), in_scope=1, unauthorized_exclusion=1
        )
        self.assertFalse(result.passed)

    def test_missing_state_is_rejected(self):
        incomplete = counts(killed=1)
        del incomplete["ignored"]
        with self.assertRaisesRegex(MutationInputError, "missingMutationState"):
            evaluate_mutation(incomplete, in_scope=1)

    def test_unknown_state_is_rejected(self):
        unknown = counts(killed=1)
        unknown["unknown"] = 0
        with self.assertRaisesRegex(MutationInputError, "unknownMutationState"):
            evaluate_mutation(unknown, in_scope=1)

    def test_state_sum_mismatch_is_rejected(self):
        with self.assertRaisesRegex(MutationInputError, "stateCountMismatch"):
            evaluate_mutation(counts(killed=1), in_scope=2)

    def test_boolean_count_is_rejected(self):
        with self.assertRaisesRegex(MutationInputError, "mutationCountNotInteger"):
            evaluate_mutation(counts(killed=True), in_scope=1)

    def test_negative_count_is_rejected(self):
        with self.assertRaisesRegex(MutationInputError, "mutationCountOutOfRange"):
            evaluate_mutation(counts(killed=-1), in_scope=-1)

    def test_json_unsafe_integer_counts_are_rejected(self):
        unsafe = 9_007_199_254_740_992
        cases = (
            (counts(killed=unsafe), unsafe, 0, "mutationCountOutOfRange"),
            (counts(), unsafe, 0, "inScopeOutOfRange"),
            (counts(killed=1), 1, unsafe, "unauthorizedExclusionOutOfRange"),
        )

        for mutation_counts, in_scope, unauthorized, error in cases:
            with self.subTest(error=error):
                with self.assertRaisesRegex(MutationInputError, error):
                    evaluate_mutation(mutation_counts, in_scope, unauthorized)

    def test_boolean_in_scope_is_rejected(self):
        with self.assertRaisesRegex(MutationInputError, "inScopeNotInteger"):
            evaluate_mutation(counts(), in_scope=False)

    def test_boolean_unauthorized_exclusion_is_rejected(self):
        with self.assertRaisesRegex(
            MutationInputError, "unauthorizedExclusionNotInteger"
        ):
            evaluate_mutation(
                counts(killed=1), in_scope=1, unauthorized_exclusion=False
            )


if __name__ == "__main__":
    unittest.main()
