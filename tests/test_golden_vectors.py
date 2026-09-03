from fractions import Fraction
import json
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
from sentinel_spec.mutation import (  # noqa: E402
    MUTATION_STATES,
    MutationInputError,
    evaluate_mutation,
)


def load_json(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8") as source:
        return json.load(source)


class CrapGoldenVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = load_json("golden/crap/formula-v1.json")

    def test_formula_cases_match_exact_fraction_decimal_and_gate(self):
        for case in self.vectors["formulaCases"]:
            with self.subTest(case=case["id"]):
                inputs = case["input"]
                expected = case["expected"]
                value = calculate_crap(
                    inputs["cyclomaticComplexity"],
                    inputs["coveredUnits"],
                    inputs["totalUnits"],
                )
                self.assertEqual(str(value.numerator), expected["numerator"])
                self.assertEqual(str(value.denominator), expected["denominator"])
                self.assertEqual(render_canonical_decimal(value), expected["decimal"])
                self.assertEqual(
                    crap_gate_passes(
                        inputs["cyclomaticComplexity"],
                        inputs["coveredUnits"],
                        inputs["totalUnits"],
                    ),
                    expected["pass"],
                )

    def test_decimal_cases_match_canonical_renderer(self):
        for case in self.vectors["decimalCases"]:
            with self.subTest(case=case["id"]):
                value = Fraction(int(case["numerator"]), int(case["denominator"]))
                self.assertEqual(render_canonical_decimal(value), case["expected"])

    def test_invalid_formula_cases_return_stable_error_codes(self):
        for case in self.vectors["invalidCases"]:
            with self.subTest(case=case["id"]):
                inputs = case["input"]
                with self.assertRaises(CrapInputError) as raised:
                    calculate_crap(
                        inputs["cyclomaticComplexity"],
                        inputs["coveredUnits"],
                        inputs["totalUnits"],
                    )
                self.assertEqual(raised.exception.code, case["error"])


class MutationGoldenVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = load_json("golden/gate/mutation-v1.json")

    def test_state_vocabulary_matches_contract(self):
        self.assertEqual(tuple(self.vectors["states"]), MUTATION_STATES)

    def test_valid_cases_match_gate_and_exact_kill_rate(self):
        for case in self.vectors["cases"]:
            with self.subTest(case=case["id"]):
                result = evaluate_mutation(
                    case["counts"],
                    case["inScope"],
                    case["unauthorizedExclusion"],
                )
                self.assertEqual(result.passed, case["expected"]["pass"])
                expected_rate = case["expected"]["killRate"]
                if expected_rate is None:
                    self.assertIsNone(result.kill_rate)
                else:
                    self.assertEqual(
                        result.kill_rate,
                        Fraction(
                            int(expected_rate["numerator"]),
                            int(expected_rate["denominator"]),
                        ),
                    )

    def test_invalid_cases_return_stable_error_codes(self):
        for case in self.vectors["invalidCases"]:
            with self.subTest(case=case["id"]):
                with self.assertRaises(MutationInputError) as raised:
                    evaluate_mutation(
                        case["counts"],
                        case["inScope"],
                        case["unauthorizedExclusion"],
                    )
                self.assertEqual(raised.exception.code, case["error"])


class ResultSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_json("schemas/result.schema.json")

    def test_schema_uses_draft_2020_12_and_closes_result_objects(self):
        self.assertEqual(
            self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )
        self.assertFalse(self.schema["additionalProperties"])
        self.assertFalse(
            self.schema["properties"]["crap"]["additionalProperties"]
        )
        self.assertFalse(
            self.schema["properties"]["mutation"]["additionalProperties"]
        )

    def test_schema_fixes_result_version_and_required_components(self):
        self.assertEqual(
            self.schema["properties"]["schemaVersion"]["const"],
            "sentinel-result-v1",
        )
        self.assertEqual(
            set(self.schema["required"]),
            {"schemaVersion", "specVersion", "crap", "mutation"},
        )

    def test_schema_uses_safe_integer_maximum_for_every_count(self):
        count_schema = self.schema["$defs"]["count"]
        self.assertEqual(count_schema["type"], "integer")
        self.assertEqual(count_schema["minimum"], 0)
        self.assertEqual(count_schema["maximum"], 9_007_199_254_740_991)

    def test_schema_uses_canonical_fraction_strings(self):
        self.assertEqual(
            self.schema["$defs"]["nonnegativeDecimalString"]["pattern"],
            "^(0|[1-9][0-9]*)$",
        )
        self.assertEqual(
            self.schema["$defs"]["positiveDecimalString"]["pattern"],
            "^[1-9][0-9]*$",
        )


if __name__ == "__main__":
    unittest.main()
