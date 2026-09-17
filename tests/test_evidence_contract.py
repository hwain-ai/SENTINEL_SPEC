import base64
import copy
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
    assign_event_ordinals,
    build_evidence_file,
    canonical_json_bytes,
    project_state_hmac,
    validate_evidence_file,
    validate_project_state_file,
)
import sentinel_spec  # noqa: E402


def load_golden(relative_path):
    return load_contract_json_bytes((ROOT / relative_path).read_bytes())


class CanonicalJsonContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = load_golden("golden/evidence/canonical-json-v1.json")

    def test_logical_values_have_exact_cross_runtime_bytes(self):
        for case in self.vectors["validCases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    canonical_json_bytes(case["value"]).hex(),
                    case["expectedHex"],
                )

    def test_invalid_logical_values_have_stable_errors(self):
        invalid_values = (
            (1.0, "canonicalJsonTypeInvalid"),
            (-1, "canonicalJsonIntegerOutOfRange"),
            (9_007_199_254_740_992, "canonicalJsonIntegerOutOfRange"),
            ({1: "not a string key"}, "canonicalJsonKeyInvalid"),
            ({"value": "\ud800"}, "canonicalJsonUnicodeScalarInvalid"),
        )
        for value, error in invalid_values:
            with self.subTest(error=error):
                with self.assertRaisesRegex(EvidenceContractError, error):
                    canonical_json_bytes(value)

    def test_reference_validators_are_public_package_contracts(self):
        expected = {
            "assign_event_ordinals",
            "build_commit_sequence_file",
            "build_evidence_file",
            "canonical_json_bytes",
            "project_state_hmac",
            "validate_commit_sequence_file",
            "validate_commit_sequence_state",
            "validate_evidence_file",
            "validate_finding_event_file",
            "validate_finding_event_records",
            "validate_project_state_file",
        }
        self.assertTrue(expected <= set(sentinel_spec.__all__))


class FindingEventSchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_golden("schemas/finding-event.schema.json")

    def test_schema_is_closed_and_matches_the_approved_event_union(self):
        self.assertEqual(
            self.schema["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(
            set(self.schema["required"]),
            {
                "defectKind",
                "diagnosticCode",
                "event",
                "findingClass",
                "findingToken",
                "fingerprintKind",
                "fingerprintVersion",
                "observationSource",
                "value",
            },
        )
        self.assertEqual(
            set(self.schema["properties"]["event"]["enum"]),
            {"detected", "persisted", "resolved", "reopened"},
        )
        self.assertEqual(
            set(self.schema["properties"]["findingClass"]["enum"]),
            {
                "backend",
                "environment",
                "projectCode",
                "projectCodeOrTest",
                "projectTest",
                "sentinel",
            },
        )
        self.assertEqual(
            set(self.schema["properties"]["fingerprintKind"]["enum"]),
            {"context", "family", "occurrence"},
        )
        self.assertEqual(
            self.schema["properties"]["observationSource"]["const"],
            "fresh",
        )


class FindingEventSemanticContractTests(unittest.TestCase):
    def setUp(self):
        self.records = self._records("a" * 64)

    @staticmethod
    def _records(token, **changes):
        common = {
            "defectKind": "crapExceeded",
            "diagnosticCode": "crapAboveThreshold",
            "event": "detected",
            "findingClass": "projectCode",
            "findingToken": token,
            "fingerprintVersion": "sentinel-fingerprint-v1",
            "observationSource": "fresh",
        }
        common.update(changes)
        values = {
            "occurrence": "1" * 64,
            "context": "2" * 64,
            "family": "3" * 64,
        }
        return [
            {**common, "fingerprintKind": kind, "value": values[kind]}
            for kind in ("occurrence", "context", "family")
        ]

    def test_single_record_file_is_canonical_and_fresh(self):
        payload = canonical_json_bytes(self.records[0]) + b"\n"

        self.assertEqual(
            sentinel_spec.validate_finding_event_file(payload),
            self.records[0],
        )
        with self.assertRaisesRegex(EvidenceContractError, "canonicalJsonMismatch"):
            sentinel_spec.validate_finding_event_file(payload[:-1])

        cached = dict(self.records[0], observationSource="cache")
        with self.assertRaisesRegex(
            EvidenceContractError,
            "findingEventObservationSourceInvalid",
        ):
            sentinel_spec.validate_finding_event_file(
                canonical_json_bytes(cached) + b"\n"
            )

    def test_record_union_rejects_unknown_fields_and_invalid_values(self):
        invalid_cases = (
            (
                {
                    name: value
                    for name, value in self.records[0].items()
                    if name != "value"
                },
                "findingEventFieldsInvalid",
            ),
            (
                {**self.records[0], "absolutePath": "/private/source.py"},
                "findingEventFieldsInvalid",
            ),
            ({**self.records[0], "event": "fixed"}, "findingEventEventInvalid"),
            ({**self.records[0], "event": []}, "findingEventEventInvalid"),
            ({**self.records[0], "findingClass": "application"}, "findingEventClassInvalid"),
            ({**self.records[0], "findingClass": []}, "findingEventClassInvalid"),
            ({**self.records[0], "defectKind": "CrapExceeded"}, "findingEventDefectKindInvalid"),
            (
                {**self.records[0], "diagnosticCode": "crap-above"},
                "findingEventDiagnosticCodeInvalid",
            ),
            ({**self.records[0], "findingToken": "A" * 64}, "findingEventTokenInvalid"),
            (
                {**self.records[0], "fingerprintKind": "location"},
                "findingEventFingerprintKindInvalid",
            ),
            ({**self.records[0], "fingerprintKind": []}, "findingEventFingerprintKindInvalid"),
            (
                {**self.records[0], "fingerprintVersion": 1},
                "findingEventFingerprintVersionInvalid",
            ),
            ({**self.records[0], "value": "1" * 63}, "findingEventFingerprintValueInvalid"),
        )
        for record, error in invalid_cases:
            with self.subTest(error=error):
                with self.assertRaisesRegex(EvidenceContractError, error):
                    sentinel_spec.validate_finding_event_records([record])

    def test_complete_fingerprint_triples_pass_for_multiple_findings(self):
        other = self._records(
            "b" * 64,
            defectKind="survivedMutant",
            diagnosticCode="mutationSurvived",
            findingClass="projectTest",
        )

        self.assertEqual(
            sentinel_spec.validate_finding_event_records(self.records + other),
            tuple(self.records + other),
        )
        self.assertEqual(sentinel_spec.validate_finding_event_records([]), ())

    def test_missing_or_duplicate_fingerprint_kind_fails_closed(self):
        with self.assertRaisesRegex(
            EvidenceContractError,
            "findingFingerprintKindsMissing",
        ):
            sentinel_spec.validate_finding_event_records(self.records[:-1])

        with self.assertRaisesRegex(
            EvidenceContractError,
            "findingFingerprintKindDuplicate",
        ):
            sentinel_spec.validate_finding_event_records(
                self.records + [dict(self.records[0])]
            )

    def test_token_collision_across_finding_identity_fails_closed(self):
        changes = (
            {"findingClass": "backend"},
            {"defectKind": "backendMalformed"},
            {"diagnosticCode": "backendReportInvalid"},
        )
        for change in changes:
            with self.subTest(change=change):
                collided = copy.deepcopy(self.records)
                collided[1].update(change)
                with self.assertRaisesRegex(
                    EvidenceContractError,
                    "findingTokenCollision",
                ):
                    sentinel_spec.validate_finding_event_records(collided)

    def test_record_collection_must_be_an_ordered_sequence(self):
        with self.assertRaisesRegex(
            EvidenceContractError,
            "findingEventRecordsInvalid",
        ):
            sentinel_spec.validate_finding_event_records("not records")


class ProjectStateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = load_golden("golden/state/project-state-v1.json")
        cls.schema = load_golden("schemas/project-state.schema.json")

    def test_schema_is_closed_and_requires_the_exact_private_fields(self):
        self.assertEqual(
            self.schema["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(
            set(self.schema["required"]),
            {
                "cleanupLeaseKey",
                "fingerprintHmacKey",
                "keyEpoch",
                "projectIdentifier",
                "schemaVersion",
                "stateVersion",
            },
        )

    def test_valid_golden_files_are_canonical_and_semantically_valid(self):
        for case in self.vectors["validCases"]:
            with self.subTest(case=case["id"]):
                payload = bytes.fromhex(case["fileHex"])
                state = validate_project_state_file(payload)
                self.assertEqual(state["keyEpoch"], case["expectedKeyEpoch"])
                self.assertEqual(
                    project_state_hmac(state),
                    case["expectedProjectStateHmac"],
                )
                self.assertEqual(payload, canonical_json_bytes(state) + b"\n")

    def test_invalid_golden_files_have_stable_errors(self):
        for case in self.vectors["invalidCases"]:
            with self.subTest(case=case["id"]):
                with self.assertRaisesRegex(EvidenceContractError, case["error"]):
                    validate_project_state_file(bytes.fromhex(case["fileHex"]))

    def test_cross_language_legacy_shapes_are_explicitly_rejected(self):
        cases = {case["id"]: case for case in self.vectors["invalidCases"]}
        expected = {
            "go-schema-version-alias",
            "clojure-control-shape",
        }
        self.assertTrue(expected <= cases.keys())
        for case_id in expected:
            with self.subTest(case=case_id):
                with self.assertRaises(EvidenceContractError):
                    validate_project_state_file(
                        bytes.fromhex(cases[case_id]["fileHex"])
                    )


class EvidenceFileContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = load_golden("golden/evidence/evidence-v1.json")
        cls.schema = load_golden("schemas/evidence.schema.json")
        cls.project_payload = bytes.fromhex(cls.vectors["projectStateFileHex"])
        cls.project_state = validate_project_state_file(cls.project_payload)

    def test_schema_is_closed_and_uses_top_level_commit_sequence(self):
        self.assertFalse(self.schema["additionalProperties"])
        self.assertIn("commitSequence", self.schema["required"])
        self.assertNotIn("run", self.schema["properties"])
        self.assertEqual(
            self.schema["properties"]["schemaVersion"]["const"],
            "sentinel-evidence-v1",
        )
        self.assertIn("hmacSha256", self.schema["required"])
        self.assertEqual(
            set(self.schema["$defs"]["crapComponent"]["required"]),
            {
                "callableCount",
                "crapMax",
                "maxDenominator",
                "maxNumerator",
                "pass",
                "unknownCount",
            },
        )

    def test_event_ids_follow_public_fingerprint_byte_order(self):
        for case in self.vectors["eventOrderingCases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    list(assign_event_ordinals(case["inputFingerprints"])),
                    case["expected"],
                )

    def test_event_ordering_rejects_invalid_or_duplicate_fingerprints(self):
        for case in self.vectors["eventOrderingInvalidCases"]:
            with self.subTest(case=case["id"]):
                with self.assertRaisesRegex(
                    EvidenceContractError,
                    case["error"],
                ):
                    assign_event_ordinals(case["inputFingerprints"])

    def test_valid_golden_bodies_produce_exact_hmac_and_file_bytes(self):
        for case in self.vectors["validCases"]:
            with self.subTest(case=case["id"]):
                body = case["body"]
                identifier = base64.urlsafe_b64decode(
                    self.project_state["projectIdentifier"] + "=="
                )
                cleanup_key = bytes.fromhex(self.vectors["cleanupLeaseKeyHex"])
                expected_state_hmac = hmac.new(
                    cleanup_key,
                    b"SENTINEL\0project-state-binding\0v1\0" + identifier,
                    hashlib.sha256,
                ).hexdigest()
                self.assertEqual(expected_state_hmac, body["projectStateHmac"])
                self.assertEqual(
                    project_state_hmac(self.project_state),
                    body["projectStateHmac"],
                )
                body_bytes = canonical_json_bytes(body)
                derived_key = hmac.new(
                    cleanup_key,
                    b"SENTINEL\0evidence-key\0v1\0",
                    hashlib.sha256,
                ).digest()
                payload = build_evidence_file(body, self.project_state)
                self.assertEqual(hashlib.sha256(body_bytes).hexdigest(), case["bodySha256"])
                self.assertEqual(derived_key.hex(), case["derivedKeyHex"])
                self.assertEqual(
                    hmac.new(
                        derived_key,
                        b"SENTINEL\0evidence\0v1\0" + body_bytes,
                        hashlib.sha256,
                    ).hexdigest(),
                    case["expectedHmac"],
                )
                self.assertEqual(hashlib.sha256(payload).hexdigest(), case["fileSha256"])
                document = validate_evidence_file(payload, self.project_state)
                self.assertEqual(document["commitSequence"], body["commitSequence"])

    def test_semantically_invalid_golden_mutations_fail_after_valid_resigning(self):
        valid_by_id = {case["id"]: case for case in self.vectors["validCases"]}
        for case in self.vectors["semanticInvalidCases"]:
            with self.subTest(case=case["id"]):
                body = copy.deepcopy(valid_by_id[case["baseCase"]]["body"])
                target = body
                path = case["field"].split(".")
                for name in path[:-1]:
                    target = target[name]
                target[path[-1]] = case["value"]
                with self.assertRaisesRegex(EvidenceContractError, case["error"]):
                    build_evidence_file(body, self.project_state)

    def test_ninety_percent_pass_round_trips_with_its_recorded_threshold(self):
        body = copy.deepcopy(self.vectors["validCases"][0]["body"])
        body["components"]["mutation"].update(
            {"inScope": 10, "killed": 9, "survived": 1, "mutationMin": "90", "pass": True}
        )
        payload = build_evidence_file(body, self.project_state)
        document = validate_evidence_file(payload, self.project_state)
        self.assertEqual(body["components"]["mutation"], document["components"]["mutation"])
        body["components"]["mutation"]["mutationMin"] = "100"
        with self.assertRaises(EvidenceContractError):
            build_evidence_file(body, self.project_state)

    def test_invalid_wire_files_have_stable_errors(self):
        valid_by_id = {case["id"]: case for case in self.vectors["validCases"]}
        for case in self.vectors["wireInvalidCases"]:
            with self.subTest(case=case["id"]):
                payload = self._invalid_wire_payload(case, valid_by_id)
                with self.assertRaisesRegex(EvidenceContractError, case["error"]):
                    validate_evidence_file(payload, self.project_state)

    def _invalid_wire_payload(self, case, valid_by_id):
        if "rawHex" in case:
            return bytes.fromhex(case["rawHex"])
        if "document" in case:
            return canonical_json_bytes(case["document"]) + b"\n"
        base = build_evidence_file(
            valid_by_id[case["baseCase"]]["body"],
            self.project_state,
        )
        document = json.loads(base)
        transform = case["transform"]
        if transform == "hmac-tamper":
            first = "0" if document["hmacSha256"][0] != "0" else "1"
            document["hmacSha256"] = first + document["hmacSha256"][1:]
            return canonical_json_bytes(document) + b"\n"
        if transform == "uppercase-hmac":
            document["hmacSha256"] = document["hmacSha256"].upper()
            return canonical_json_bytes(document) + b"\n"
        if transform == "rename-hmac":
            document["hmac"] = document.pop("hmacSha256")
            return canonical_json_bytes(document) + b"\n"
        if transform == "whitespace":
            return json.dumps(document, sort_keys=True).encode("utf-8") + b"\n"
        if transform == "missing-lf":
            return canonical_json_bytes(document)
        self.fail(f"unknown wire transform: {transform}")

    def test_manifest_count_filename_and_digest_are_semantically_joined(self):
        body = copy.deepcopy(self.vectors["validCases"][0]["body"])
        invalid_manifests = (
            ("eventCount", 2, "eventManifestCountMismatch"),
            (
                "events",
                [{"filename": "../event.json", "sha256": "a" * 64}],
                "eventManifestFilenameInvalid",
            ),
        )
        for field, value, error in invalid_manifests:
            with self.subTest(error=error):
                invalid = copy.deepcopy(body)
                invalid[field] = value
                with self.assertRaisesRegex(EvidenceContractError, error):
                    build_evidence_file(invalid, self.project_state)

        duplicate = copy.deepcopy(body)
        duplicate["eventCount"] = 2
        duplicate["events"] = duplicate["events"] * 2
        with self.assertRaisesRegex(
            EvidenceContractError,
            "eventManifestDuplicate",
        ):
            build_evidence_file(duplicate, self.project_state)

    def test_manifest_filenames_are_one_based_contiguous_32_hex_ordinals(self):
        body = copy.deepcopy(self.vectors["validCases"][0]["body"])
        body["events"][0]["filename"] = "00000000000000000000000000000002.json"

        with self.assertRaisesRegex(
            EvidenceContractError,
            "eventManifestOrdinalInvalid",
        ):
            build_evidence_file(body, self.project_state)

    def test_evidence_revalidates_the_complete_project_state_contract(self):
        body = copy.deepcopy(self.vectors["validCases"][0]["body"])
        invalid_state = dict(self.project_state)
        invalid_state["schemaVersion"] = "project-state-v1"

        with self.assertRaisesRegex(
            EvidenceContractError,
            "projectStateSchemaVersionInvalid",
        ):
            build_evidence_file(body, invalid_state)

    def test_project_binding_survives_fingerprint_key_rotation(self):
        body = copy.deepcopy(self.vectors["validCases"][0]["body"])
        payload = build_evidence_file(body, self.project_state)
        rotated_state = dict(self.project_state)
        rotated_state["fingerprintHmacKey"] = (
            base64.urlsafe_b64encode(bytes(range(64, 96)))
            .rstrip(b"=")
            .decode("ascii")
        )
        rotated_state["keyEpoch"] = 2

        self.assertEqual(
            project_state_hmac(self.project_state),
            project_state_hmac(rotated_state),
        )
        self.assertEqual(
            validate_evidence_file(payload, rotated_state)["keyEpoch"],
            1,
        )

    def test_evidence_epoch_cannot_be_ahead_of_project_state(self):
        body = copy.deepcopy(self.vectors["validCases"][0]["body"])
        body["keyEpoch"] = 2

        with self.assertRaisesRegex(EvidenceContractError, "keyEpochInvalid"):
            build_evidence_file(body, self.project_state)

    def test_new_evidence_cannot_claim_a_stale_key_epoch(self):
        body = copy.deepcopy(self.vectors["validCases"][0]["body"])
        rotated_state = dict(self.project_state)
        rotated_state["fingerprintHmacKey"] = (
            base64.urlsafe_b64encode(bytes(range(64, 96)))
            .rstrip(b"=")
            .decode("ascii")
        )
        rotated_state["keyEpoch"] = 2

        with self.assertRaisesRegex(EvidenceContractError, "keyEpochInvalid"):
            build_evidence_file(body, rotated_state)

    def test_crap_component_requires_canonical_reduced_fraction(self):
        base = copy.deepcopy(self.vectors["validCases"][0]["body"])
        invalid_components = (
            ({"maxNumerator": "16", "maxDenominator": "2"}, "crapComponentFractionInvalid"),
            ({"maxNumerator": "0", "maxDenominator": "2"}, "crapComponentFractionInvalid"),
            ({"maxNumerator": "1" * 97, "maxDenominator": "1"}, "crapComponentInvalid"),
            ({"maxNumerator": "1", "maxDenominator": "1" * 49}, "crapComponentInvalid"),
        )
        for changes, error in invalid_components:
            with self.subTest(changes=changes):
                body = copy.deepcopy(base)
                body["components"]["crap"].update(changes)
                with self.assertRaisesRegex(EvidenceContractError, error):
                    build_evidence_file(body, self.project_state)

    def test_empty_callable_inventory_is_validly_represented_as_failure(self):
        body = copy.deepcopy(self.vectors["validCases"][0]["body"])
        body["command"] = "crap"
        body["certification"] = False
        body["terminalStatus"] = "qualityFailed"
        body["exitCode"] = 2
        body["components"] = {
            "crap": {
                "callableCount": 0,
                "crapMax": "8",
                "maxNumerator": "0",
                "maxDenominator": "1",
                "pass": False,
                "unknownCount": 0,
            }
        }

        document = validate_evidence_file(
            build_evidence_file(body, self.project_state),
            self.project_state,
        )
        self.assertFalse(document["components"]["crap"]["pass"])

    def test_crap_maximum_matches_empty_or_nonempty_inventory(self):
        base = copy.deepcopy(self.vectors["validCases"][0]["body"])
        invalid_components = (
            {
                "callableCount": 0,
                "crapMax": "8",
                "maxNumerator": "8",
                "maxDenominator": "1",
                "pass": False,
                "unknownCount": 0,
            },
            {
                "callableCount": 1,
                "crapMax": "8",
                "maxNumerator": "0",
                "maxDenominator": "1",
                "pass": True,
                "unknownCount": 0,
            },
        )
        for component in invalid_components:
            with self.subTest(component=component):
                body = copy.deepcopy(base)
                body["components"]["crap"] = component
                with self.assertRaisesRegex(
                    EvidenceContractError,
                    "crapComponentInventoryInvalid",
                ):
                    build_evidence_file(body, self.project_state)

    def test_all_unknown_callable_inventory_uses_zero_known_maximum(self):
        body = copy.deepcopy(self.vectors["validCases"][0]["body"])
        body["command"] = "crap"
        body["certification"] = False
        body["terminalStatus"] = "qualityFailed"
        body["exitCode"] = 2
        body["components"] = {
            "crap": {
                "callableCount": 1,
                "crapMax": "8",
                "maxNumerator": "0",
                "maxDenominator": "1",
                "pass": False,
                "unknownCount": 1,
            }
        }

        validate_evidence_file(
            build_evidence_file(body, self.project_state),
            self.project_state,
        )

    def test_terminal_status_and_component_results_cannot_disagree(self):
        body = copy.deepcopy(self.vectors["validCases"][0]["body"])
        body["terminalStatus"] = "qualityFailed"
        body["exitCode"] = 2

        with self.assertRaisesRegex(
            EvidenceContractError,
            "terminalComponentMismatch",
        ):
            build_evidence_file(body, self.project_state)

    def test_mutant_tool_error_uses_backend_error_precedence(self):
        body = copy.deepcopy(self.vectors["validCases"][1]["body"])
        mutation = body["components"]["mutation"]
        mutation["survived"] = 0
        mutation["toolError"] = 1

        with self.assertRaisesRegex(
            EvidenceContractError,
            "terminalStatusPrecedenceInvalid",
        ):
            build_evidence_file(body, self.project_state)

    def test_cache_observation_cannot_claim_new_finding_events(self):
        body = copy.deepcopy(self.vectors["validCases"][2]["body"])
        body["eventCount"] = 1
        body["events"] = [
            {
                "filename": "00000000000000000000000000000001.json",
                "sha256": "a" * 64,
            }
        ]

        with self.assertRaisesRegex(
            EvidenceContractError,
            "cacheObservationHasEvents",
        ):
            build_evidence_file(body, self.project_state)

    def test_strict_evidence_cannot_use_a_cached_observation(self):
        body = copy.deepcopy(self.vectors["validCases"][2]["body"])
        body["mode"] = "strict"

        with self.assertRaisesRegex(
            EvidenceContractError,
            "strictCacheInvalid",
        ):
            build_evidence_file(body, self.project_state)

    def test_schema_contains_no_secret_or_raw_path_fields(self):
        encoded = json.dumps(self.schema, sort_keys=True)
        for forbidden in (
            '"cleanupLeaseKey"',
            '"fingerprintHmacKey"',
            '"projectIdentifier"',
            '"absolutePath"',
            '"stdout"',
            '"stderr"',
            '"source"',
            '"replacement"',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, encoded)


if __name__ == "__main__":
    unittest.main()
