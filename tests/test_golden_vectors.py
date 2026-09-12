from fractions import Fraction
import json
import math
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
from sentinel_spec.contract_json import (  # noqa: E402
    ContractJsonError,
    load_contract_json_bytes,
)


def load_json(relative_path):
    return load_contract_json_bytes((ROOT / relative_path).read_bytes())


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
                numerator = int(case["numerator"])
                denominator = int(case["denominator"])
                self.assertEqual(1, math.gcd(numerator, denominator))
                value = Fraction(numerator, denominator)
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

    def test_raw_formula_inputs_fail_before_lossy_number_parsing(self):
        for case in self.vectors["rawJsonInvalidCases"]:
            with self.subTest(case=case["id"]):
                with self.assertRaises(ContractJsonError) as raised:
                    load_contract_json_bytes(case["rawInput"].encode("utf-8"))
                self.assertEqual(raised.exception.code, case["jsonError"])

                exact_input = json.loads(case["rawInput"])
                with self.assertRaises(CrapInputError) as semantic_error:
                    calculate_crap(
                        exact_input["cyclomaticComplexity"],
                        exact_input["coveredUnits"],
                        exact_input["totalUnits"],
                    )
                self.assertEqual(
                    semantic_error.exception.code,
                    case["semanticError"],
                )

    def test_vectors_pin_large_and_unsafe_plus_one_boundaries(self):
        formula_by_id = {case["id"]: case for case in self.vectors["formulaCases"]}
        raw_invalid_by_id = {
            case["id"]: case for case in self.vectors["rawJsonInvalidCases"]
        }
        decimal_by_id = {case["id"]: case for case in self.vectors["decimalCases"]}

        large_formula = formula_by_id["maximum-json-safe-partial-coverage"]
        self.assertEqual(
            48,
            len(large_formula["expected"]["numerator"]),
        )
        large_decimal = decimal_by_id["eighty-by-forty-eight-digit-fraction"]
        self.assertEqual(80, len(large_decimal["numerator"]))
        self.assertEqual(48, len(large_decimal["denominator"]))

        plus_one_ids = {
            "json-unsafe-complexity-plus-one",
            "json-unsafe-covered-units-plus-one",
            "json-unsafe-total-units-plus-one",
        }
        self.assertTrue(plus_one_ids <= raw_invalid_by_id.keys())
        for case_id in plus_one_ids:
            self.assertIn("9007199254740993", raw_invalid_by_id[case_id]["rawInput"])


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

    def test_raw_mutation_inputs_fail_before_lossy_number_parsing(self):
        for case in self.vectors["rawJsonInvalidCases"]:
            with self.subTest(case=case["id"]):
                with self.assertRaises(ContractJsonError) as raised:
                    load_contract_json_bytes(case["rawInput"].encode("utf-8"))
                self.assertEqual(raised.exception.code, case["jsonError"])

                exact_input = json.loads(case["rawInput"])
                with self.assertRaises(MutationInputError) as semantic_error:
                    evaluate_mutation(
                        exact_input["counts"],
                        exact_input["inScope"],
                        exact_input["unauthorizedExclusion"],
                    )
                self.assertEqual(
                    semantic_error.exception.code,
                    case["semanticError"],
                )

    def test_vectors_pin_nontrivial_maximum_and_unsafe_plus_one_boundaries(self):
        case_by_id = {case["id"]: case for case in self.vectors["cases"]}
        raw_invalid_by_id = {
            case["id"]: case for case in self.vectors["rawJsonInvalidCases"]
        }

        near_maximum = case_by_id["maximum-json-safe-one-survived"]
        self.assertEqual(
            {
                "numerator": "9007199254740990",
                "denominator": "9007199254740991",
            },
            near_maximum["expected"]["killRate"],
        )
        plus_one_ids = {
            "json-unsafe-mutation-count-plus-one",
            "json-unsafe-in-scope-plus-one",
            "json-unsafe-unauthorized-exclusion-plus-one",
        }
        self.assertTrue(plus_one_ids <= raw_invalid_by_id.keys())
        for case_id in plus_one_ids:
            self.assertIn("9007199254740993", raw_invalid_by_id[case_id]["rawInput"])


class ContractJsonLoaderTests(unittest.TestCase):
    def test_requires_raw_bytes(self):
        for payload in ('{"value":1}', bytearray(b'{"value":1}')):
            with self.subTest(payload_type=type(payload).__name__):
                with self.assertRaisesRegex(
                    ContractJsonError,
                    "jsonBytesRequired",
                ):
                    load_contract_json_bytes(payload)

    def test_rejects_invalid_utf8(self):
        with self.assertRaisesRegex(ContractJsonError, "jsonUtf8Invalid"):
            load_contract_json_bytes(b'{"value":"\xff"}')

    def test_rejects_utf8_bom(self):
        with self.assertRaisesRegex(ContractJsonError, "jsonBomForbidden"):
            load_contract_json_bytes(b"\xef\xbb\xbf{}")

    def test_rejects_malformed_json(self):
        with self.assertRaisesRegex(ContractJsonError, "jsonSyntaxInvalid"):
            load_contract_json_bytes(b'{"value":}')

    def test_rejects_nonstandard_numeric_constants(self):
        with self.assertRaisesRegex(
            ContractJsonError,
            "jsonIntegerLexemeInvalid",
        ):
            load_contract_json_bytes(b'{"value":NaN}')

    def test_rejects_duplicate_keys_before_object_mapping(self):
        with self.assertRaisesRegex(ContractJsonError, "jsonDuplicateKey"):
            load_contract_json_bytes(b'{"value":1,"value":2}')

    def test_rejects_noninteger_numeric_lexemes(self):
        for token in (b"1.0", b"1e0", b"-0"):
            with self.subTest(token=token):
                with self.assertRaisesRegex(
                    ContractJsonError,
                    "jsonIntegerLexemeInvalid",
                ):
                    load_contract_json_bytes(b'{"value":' + token + b"}")

    def test_rejects_non_json_integer_lexemes_as_syntax_errors(self):
        for token in (b"01", b"+1", b"1_0"):
            with self.subTest(token=token):
                with self.assertRaisesRegex(
                    ContractJsonError,
                    "jsonSyntaxInvalid",
                ):
                    load_contract_json_bytes(b'{"value":' + token + b"}")

    def test_rejects_unsafe_integer_before_native_conversion(self):
        for token in (
            b"9007199254740992",
            b"9007199254740993",
            b"10000000000000000000000000000000000000000",
        ):
            with self.subTest(token=token):
                with self.assertRaisesRegex(
                    ContractJsonError,
                    "jsonIntegerOutOfRange",
                ):
                    load_contract_json_bytes(b'{"value":' + token + b"}")

    def test_accepts_exact_safe_integer_boundaries(self):
        document = load_contract_json_bytes(
            b'{"minimum":-9007199254740991,"maximum":9007199254740991}'
        )

        self.assertEqual(-9_007_199_254_740_991, document["minimum"])
        self.assertEqual(9_007_199_254_740_991, document["maximum"])


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
