import hashlib
import hmac
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_spec.contract_json import load_contract_json_bytes  # noqa: E402
from sentinel_spec.evidence_contract import (  # noqa: E402
    EvidenceContractError,
    build_commit_sequence_file,
    validate_commit_sequence_file,
    validate_commit_sequence_state,
)


def load_golden(relative_path):
    return load_contract_json_bytes((ROOT / relative_path).read_bytes())


class CommitSequenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = load_golden("golden/commit-sequence/commit-sequence-v1.json")
        cls.schema = load_golden("schemas/commit-sequence.schema.json")
        cls.cleanup_key = bytes.fromhex(cls.vectors["cleanupLeaseKeyHex"])

    def test_schema_is_closed_and_uses_positive_uint64_decimal_text(self):
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(
            set(self.schema["required"]),
            {"version", "lastAllocated", "hmacSha256"},
        )
        self.assertEqual(
            self.schema["properties"]["lastAllocated"]["pattern"],
            "^[1-9][0-9]{0,19}$",
        )

    def test_valid_golden_cases_pin_derived_key_mac_input_and_file(self):
        for case in self.vectors["validCases"]:
            with self.subTest(case=case["id"]):
                body = {
                    "lastAllocated": case["lastAllocated"],
                    "version": "commit-sequence-v1",
                }
                body_bytes = json.dumps(
                    body,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("ascii")
                derived_key = hmac.new(
                    self.cleanup_key,
                    b"SENTINEL\0commit-sequence-key\0v1\0",
                    hashlib.sha256,
                ).digest()
                mac_input = b"SENTINEL\0commit-sequence\0v1\0" + body_bytes
                expected_hmac = hmac.new(
                    derived_key,
                    mac_input,
                    hashlib.sha256,
                ).hexdigest()
                self.assertEqual(body_bytes.hex(), case["bodyHex"])
                self.assertEqual(derived_key.hex(), case["derivedKeyHex"])
                self.assertEqual(mac_input.hex(), case["macInputHex"])
                self.assertEqual(expected_hmac, case["expectedHmac"])
                payload = build_commit_sequence_file(
                    case["lastAllocated"],
                    self.cleanup_key,
                )
                self.assertEqual(payload.hex(), case["fileHex"])
                self.assertEqual(
                    validate_commit_sequence_file(payload, self.cleanup_key),
                    int(case["lastAllocated"]),
                )

    def test_invalid_golden_files_have_stable_errors(self):
        for case in self.vectors["invalidCases"]:
            with self.subTest(case=case["id"]):
                with self.assertRaisesRegex(EvidenceContractError, case["error"]):
                    validate_commit_sequence_file(
                        bytes.fromhex(case["fileHex"]),
                        self.cleanup_key,
                    )

    def test_cross_language_hmac_alias_and_zero_are_rejected(self):
        cases = {case["id"]: case for case in self.vectors["invalidCases"]}
        for case_id in ("clojure-hmac-field-alias", "clojure-zero-sequence"):
            with self.subTest(case=case_id):
                with self.assertRaises(EvidenceContractError):
                    validate_commit_sequence_file(
                        bytes.fromhex(cases[case_id]["fileHex"]),
                        self.cleanup_key,
                    )

    def test_high_water_semantics_allow_gaps_but_reject_rollback(self):
        for case in self.vectors["stateCases"]:
            with self.subTest(case=case["id"]):
                payload = (
                    None
                    if case["lastAllocated"] is None
                    else build_commit_sequence_file(
                        case["lastAllocated"],
                        self.cleanup_key,
                    )
                )
                if "error" in case:
                    with self.assertRaisesRegex(EvidenceContractError, case["error"]):
                        validate_commit_sequence_state(
                            payload,
                            self.cleanup_key,
                            case["completedSequences"],
                            case["retentionHighWaters"],
                        )
                else:
                    self.assertEqual(
                        validate_commit_sequence_state(
                            payload,
                            self.cleanup_key,
                            case["completedSequences"],
                            case["retentionHighWaters"],
                        ),
                        case["expectedLastAllocated"],
                    )


if __name__ == "__main__":
    unittest.main()
