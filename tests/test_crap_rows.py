import re
import sys
import unittest
from functools import cmp_to_key
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from sentinel_spec.crap_rows import (  # noqa: E402
    CrapRow,
    CrapRowError,
    sort_crap_rows,
)
from sentinel_spec.contract_json import (  # noqa: E402
    ContractJsonError,
    load_contract_json_bytes,
)


_KNOWN_ROW_FIELDS = frozenset(
    {
        "moduleRelativePath",
        "sourceStartByte",
        "callableId",
        "numerator",
        "denominator",
    }
)
_UNKNOWN_ROW_FIELDS = frozenset(
    {
        "moduleRelativePath",
        "sourceStartByte",
        "callableId",
        "unknownReason",
    }
)
_NONNEGATIVE_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)")
_POSITIVE_DECIMAL = re.compile(r"[1-9][0-9]*")


def _parse_decimal_string(name, value, pattern):
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise CrapRowError(f"{name}Invalid")
    return int(value)


def _row_from_json(row):
    if not isinstance(row, dict):
        raise CrapRowError("rowShapeInvalid")
    fields = frozenset(row)
    if fields == _UNKNOWN_ROW_FIELDS:
        return CrapRow.unknown(
            row["moduleRelativePath"],
            row["sourceStartByte"],
            row["callableId"],
            row["unknownReason"],
        )
    if fields != _KNOWN_ROW_FIELDS:
        raise CrapRowError("rowShapeInvalid")
    return CrapRow.known(
        row["moduleRelativePath"],
        row["sourceStartByte"],
        row["callableId"],
        _parse_decimal_string("numerator", row["numerator"], _NONNEGATIVE_DECIMAL),
        _parse_decimal_string("denominator", row["denominator"], _POSITIVE_DECIMAL),
    )


def _load_json_file(relative_path):
    return load_contract_json_bytes((REPOSITORY_ROOT / relative_path).read_bytes())


def _identity_compare(left, right, callable_key):
    left_key = (
        left["moduleRelativePath"].encode("utf-8"),
        left["sourceStartByte"],
        callable_key(left["callableId"]),
    )
    right_key = (
        right["moduleRelativePath"].encode("utf-8"),
        right["sourceStartByte"],
        callable_key(right["callableId"]),
    )
    return (left_key > right_key) - (left_key < right_key)


def _compare_with_float_risk(left, right):
    left_unknown = "unknownReason" in left
    right_unknown = "unknownReason" in right
    if left_unknown != right_unknown:
        return -1 if left_unknown else 1
    if not left_unknown:
        left_risk = float(left["numerator"]) / float(left["denominator"])
        right_risk = float(right["numerator"]) / float(right["denominator"])
        if left_risk != right_risk:
            return -1 if left_risk > right_risk else 1
    return _identity_compare(left, right, lambda value: value.encode("utf-8"))


def _compare_with_utf16_callable_id(left, right):
    left_unknown = "unknownReason" in left
    right_unknown = "unknownReason" in right
    if left_unknown != right_unknown:
        return -1 if left_unknown else 1
    if not left_unknown:
        comparison = (
            int(left["numerator"]) * int(right["denominator"])
            - int(right["numerator"]) * int(left["denominator"])
        )
        if comparison:
            return -1 if comparison > 0 else 1
    return _identity_compare(left, right, lambda value: value.encode("utf-16-be"))


def _compare_preserving_unknown_input_order(left, right):
    left_unknown = "unknownReason" in left
    right_unknown = "unknownReason" in right
    if left_unknown != right_unknown:
        return -1 if left_unknown else 1
    if left_unknown:
        return 0
    comparison = (
        int(left["numerator"]) * int(right["denominator"])
        - int(right["numerator"]) * int(left["denominator"])
    )
    if comparison:
        return -1 if comparison > 0 else 1
    return _identity_compare(left, right, lambda value: value.encode("utf-8"))


class CrapRowOrderingTests(unittest.TestCase):
    def test_golden_vectors_define_the_same_total_order(self):
        document = _load_json_file("golden/crap/stable-sort-v1.json")

        self.assertEqual("sentinel-crap-row-order-v1", document["schemaVersion"])
        for case in document["cases"]:
            with self.subTest(case=case["id"]):
                rows = tuple(_row_from_json(row) for row in case["rows"])
                self.assertEqual(
                    tuple(case["expectedCallableIds"]),
                    tuple(row.callable_id for row in sort_crap_rows(rows)),
                )
        for case in document["invalidCases"]:
            with self.subTest(case=case["id"]):
                with self.assertRaisesRegex(CrapRowError, case["expectedError"]):
                    rows = tuple(_row_from_json(row) for row in case["rows"])
                    sort_crap_rows(rows)

    def test_golden_pins_strict_wire_and_identity_errors(self):
        document = _load_json_file("golden/crap/stable-sort-v1.json")
        invalid_by_id = {case["id"]: case for case in document["invalidCases"]}
        required = {
            "duplicate-identity-with-different-risk",
            "leading-zero-numerator",
            "leading-plus-numerator",
            "leading-space-numerator",
            "underscore-numerator",
            "leading-zero-denominator",
            "unexpected-row-property",
            "mixed-known-and-unknown-fields",
            "unreduced-known-fraction",
        }
        self.assertTrue(required <= invalid_by_id.keys())
        duplicate_rows = invalid_by_id["duplicate-identity-with-different-risk"][
            "rows"
        ]
        self.assertNotEqual(
            (duplicate_rows[0]["numerator"], duplicate_rows[0]["denominator"]),
            (duplicate_rows[1]["numerator"], duplicate_rows[1]["denominator"]),
        )

    def test_golden_rejects_float_risk_comparator(self):
        self._assert_golden_rejects(
            "exact-cross-multiply-exceeds-fixed-width",
            _compare_with_float_risk,
        )

    def test_golden_rejects_utf16_callable_id_comparator(self):
        self._assert_golden_rejects(
            "callable-id-utf8-byte-order-differs-from-utf16",
            _compare_with_utf16_callable_id,
        )

    def test_golden_rejects_unknown_input_order_comparator(self):
        self._assert_golden_rejects(
            "unknown-rows-use-identity-not-input-order",
            _compare_preserving_unknown_input_order,
        )

    def _assert_golden_rejects(self, case_id, comparator):
        document = _load_json_file("golden/crap/stable-sort-v1.json")
        case = next(case for case in document["cases"] if case["id"] == case_id)
        actual = tuple(
            row["callableId"]
            for row in sorted(case["rows"], key=cmp_to_key(comparator))
        )
        self.assertNotEqual(
            tuple(case["expectedCallableIds"]),
            actual,
            "forbidden comparator passed its distinguishing golden case",
        )

    def test_row_loader_rejects_noncanonical_decimal_strings(self):
        base = {
            "moduleRelativePath": "src/a.py",
            "sourceStartByte": 0,
            "callableId": "a",
            "numerator": "1",
            "denominator": "1",
        }
        invalid_fields = (
            ("numerator", "01", "numeratorInvalid"),
            ("numerator", "+1", "numeratorInvalid"),
            ("numerator", " 1", "numeratorInvalid"),
            ("numerator", "1_0", "numeratorInvalid"),
            ("denominator", "01", "denominatorInvalid"),
        )
        for field, value, error in invalid_fields:
            with self.subTest(field=field, value=value):
                row = dict(base)
                row[field] = value
                with self.assertRaisesRegex(CrapRowError, error):
                    _row_from_json(row)

    def test_row_loader_rejects_extra_and_mixed_fields(self):
        known = {
            "moduleRelativePath": "src/a.py",
            "sourceStartByte": 0,
            "callableId": "a",
            "numerator": "1",
            "denominator": "1",
        }
        malformed_rows = (
            dict(known, unexpected="ignored"),
            dict(known, unknownReason="coverageFileMissing"),
        )
        for row in malformed_rows:
            with self.subTest(row=row):
                with self.assertRaisesRegex(CrapRowError, "rowShapeInvalid"):
                    _row_from_json(row)

    def test_raw_row_loader_rejects_duplicate_numerator_before_mapping(self):
        raw_row = (
            b'{"moduleRelativePath":"src/a.py","sourceStartByte":0,'
            b'"callableId":"a","numerator":"2","numerator":"1",'
            b'"denominator":"1"}'
        )

        with self.assertRaisesRegex(ContractJsonError, "jsonDuplicateKey"):
            _row_from_json(load_contract_json_bytes(raw_row))

    def test_raw_golden_cases_reject_lexical_and_unsafe_integers(self):
        document = _load_json_file("golden/crap/stable-sort-v1.json")
        raw_by_id = {case["id"]: case for case in document["rawJsonInvalidCases"]}
        required = {
            "duplicate-numerator-json-key",
            "fractional-source-start",
            "exponent-source-start",
            "negative-zero-source-start",
            "leading-zero-source-start",
            "leading-plus-source-start",
            "underscore-source-start",
            "source-start-two-to-the-53",
            "source-start-two-to-the-53-plus-one",
        }

        self.assertTrue(required <= raw_by_id.keys())
        for case_id in required:
            case = raw_by_id[case_id]
            with self.subTest(case=case_id):
                with self.assertRaisesRegex(
                    ContractJsonError,
                    case["expectedError"],
                ):
                    load_contract_json_bytes(case["rawDocument"].encode("utf-8"))

    def test_contract_uses_module_relative_path_term(self):
        contract = (REPOSITORY_ROOT / "contracts" / "crap.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("module-relative POSIX path", contract)
        self.assertNotIn("project-relative POSIX path", contract)

    def test_sorts_unknown_then_exact_risk_then_stable_identity(self):
        rows = (
            CrapRow.known("src/low.py", 2, "low", 1, 3),
            CrapRow.known(
                "src/near-high.py",
                5,
                "near-high",
                1_000_000_000_000_001,
                3_000_000_000_000_000,
            ),
            CrapRow.unknown("src/한글.py", 7, "unknown-korean", "coverageFileMissing"),
            CrapRow.known("src/high.py", 1, "high", 9, 1),
            CrapRow.unknown("src/𐀀.py", 3, "unknown-astral", "coverageUnitsMissing"),
        )

        ordered = sort_crap_rows(rows)

        self.assertEqual(
            (
                "unknown-korean",
                "unknown-astral",
                "high",
                "near-high",
                "low",
            ),
            tuple(row.callable_id for row in ordered),
        )
        self.assertEqual(rows, tuple(rows), "sorting must not mutate caller input")

    def test_compares_fraction_instead_of_rounded_decimal(self):
        exact_third = CrapRow.known("src/b.py", 1, "exact-third", 1, 3)
        slightly_higher = CrapRow.known(
            "src/a.py",
            1,
            "slightly-higher",
            1_000_000_000_000_001,
            3_000_000_000_000_000,
        )

        ordered = sort_crap_rows((exact_third, slightly_higher))

        self.assertEqual(
            ("slightly-higher", "exact-third"),
            tuple(row.callable_id for row in ordered),
        )

    def test_uses_start_byte_then_callable_id_as_final_tie_breakers(self):
        rows = (
            CrapRow.known("src/same.py", 2, "z", 2, 1),
            CrapRow.known("src/same.py", 1, "z", 2, 1),
            CrapRow.known("src/same.py", 1, "a", 2, 1),
        )

        ordered = sort_crap_rows(rows)

        self.assertEqual(
            ((1, "a"), (1, "z"), (2, "z")),
            tuple((row.source_start_byte, row.callable_id) for row in ordered),
        )

    def test_rejects_duplicate_final_identity_key(self):
        duplicate = CrapRow.known("src/same.py", 1, "same", 2, 1)

        with self.assertRaisesRegex(CrapRowError, "identityAmbiguous"):
            sort_crap_rows((duplicate, duplicate))

    def test_limits_source_start_to_json_safe_integer_range(self):
        maximum = 9_007_199_254_740_991

        row = CrapRow.known("src/a.py", maximum, "a", 1, 1)

        self.assertEqual(maximum, row.source_start_byte)
        for invalid in (maximum + 1, maximum + 2):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(CrapRowError, "sourceStartByteInvalid"):
                    CrapRow.known("src/a.py", invalid, "a", 1, 1)

    def test_rejects_noncanonical_rows(self):
        invalid_factories = (
            lambda: CrapRow.known("./src/a.py", 1, "a", 1, 1),
            lambda: CrapRow.known("src/a.py", -1, "a", 1, 1),
            lambda: CrapRow.known("src/a.py", 1, "", 1, 1),
            lambda: CrapRow.known("src/a.py", 1, "a", -1, 1),
            lambda: CrapRow.known("src/a.py", 1, "a", 1, 0),
            lambda: CrapRow.unknown("src/a.py", 1, "a", ""),
        )

        for factory in invalid_factories:
            with self.subTest(factory=factory):
                with self.assertRaises(CrapRowError):
                    factory()

    def test_direct_constructor_cannot_bypass_known_unknown_invariants(self):
        invalid_rows = (
            (1, None, None),
            (-1, 1, None),
            (2, 2, None),
            (None, None, ""),
            (1, 1, "coverageFileMissing"),
        )

        for numerator, denominator, unknown_reason in invalid_rows:
            with self.subTest(
                numerator=numerator,
                denominator=denominator,
                unknown_reason=unknown_reason,
            ):
                with self.assertRaises(CrapRowError):
                    CrapRow(
                        module_relative_path="src/a.py",
                        source_start_byte=0,
                        callable_id="a",
                        numerator=numerator,
                        denominator=denominator,
                        unknown_reason=unknown_reason,
                    )


if __name__ == "__main__":
    unittest.main()
