"""Executable byte and semantic contracts for SENTINEL private evidence."""

from __future__ import annotations

import base64
import calendar
import hashlib
import hmac
import math
import re
import uuid
from datetime import datetime
from typing import Mapping, Optional, Sequence, Tuple

from .contract_json import ContractJsonError, load_contract_json_bytes
from .mutation import MUTATION_STATES, MutationInputError, evaluate_mutation


MAX_SAFE_INTEGER = 9_007_199_254_740_991
MAX_UINT64 = 18_446_744_073_709_551_615

_PROJECT_FIELDS = {
    "cleanupLeaseKey",
    "fingerprintHmacKey",
    "keyEpoch",
    "projectIdentifier",
    "schemaVersion",
    "stateVersion",
}
_EVIDENCE_BODY_FIELDS = {
    "certification",
    "command",
    "commitSequence",
    "committedAtUtc",
    "completedAtUtc",
    "components",
    "correlationId",
    "diagnosticCodes",
    "eventCount",
    "events",
    "exitCode",
    "fingerprintVersion",
    "keyEpoch",
    "language",
    "mode",
    "observationSource",
    "projectStateHmac",
    "runId",
    "schemaVersion",
    "sourceRunId",
    "specVersion",
    "startedAtUtc",
    "startedSha256",
    "terminalStatus",
}
_CRAP_FIELDS = {
    "callableCount",
    "maxNumerator",
    "maxDenominator",
    "pass",
    "unknownCount",
}
_MUTATION_FIELDS = set(MUTATION_STATES) | {
    "inScope",
    "pass",
    "unauthorizedExclusion",
}
_FINDING_EVENT_FIELDS = {
    "defectKind",
    "diagnosticCode",
    "event",
    "findingClass",
    "findingToken",
    "fingerprintKind",
    "fingerprintVersion",
    "observationSource",
    "value",
}
_FINDING_EVENTS = {"detected", "persisted", "resolved", "reopened"}
_FINDING_CLASSES = {
    "backend",
    "environment",
    "projectCode",
    "projectCodeOrTest",
    "projectTest",
    "sentinel",
}
_FINGERPRINT_KINDS = {"occurrence", "context", "family"}
_SEQUENCE_KEY_DOMAIN = b"SENTINEL\0commit-sequence-key\0v1\0"
_SEQUENCE_MAC_DOMAIN = b"SENTINEL\0commit-sequence\0v1\0"
_EVIDENCE_KEY_DOMAIN = b"SENTINEL\0evidence-key\0v1\0"
_EVIDENCE_MAC_DOMAIN = b"SENTINEL\0evidence\0v1\0"
_PROJECT_STATE_DOMAIN = b"SENTINEL\0project-state-binding\0v1\0"
_HEX_256 = re.compile(r"^[0-9a-f]{64}$")
_BASE64URL = re.compile(r"^[A-Za-z0-9_-]+$")
_UINT64 = re.compile(r"^[1-9][0-9]*$")
_UINT64_ZERO = re.compile(r"^(?:0|[1-9][0-9]*)$")
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")
_SAFE_CODE = re.compile(r"^[a-z][A-Za-z0-9]{0,63}$")
_EVENT_FILENAME = re.compile(r"^[0-9a-f]{32}\.json$")
_PUBLIC_FINGERPRINT = re.compile(r"^hmac-sha256:[0-9a-f]{64}$")
_UTC = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.([0-9]{1,9}))?Z$"
)
_TERMINAL_EXIT = {
    "passed": 0,
    "toolError": 1,
    "qualityFailed": 2,
    "baselineFailed": 4,
    "dependencyError": 5,
    "backendError": 6,
    "evidenceError": 7,
    "cancelled": 8,
}


class EvidenceContractError(ValueError):
    """A private state or evidence byte contract was violated."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def canonical_json_bytes(value: object) -> bytes:
    """Encode one logical value using sentinel-fingerprint-json-v1."""

    return _encode_json(value)


def assign_event_ordinals(fingerprints: Sequence[str]) -> tuple:
    """Sort public fingerprints and assign run-local one-based event filenames."""

    if not isinstance(fingerprints, (list, tuple)):
        raise EvidenceContractError("findingFingerprintsInvalid")
    if any(
        not isinstance(value, str)
        or _PUBLIC_FINGERPRINT.fullmatch(value) is None
        for value in fingerprints
    ):
        raise EvidenceContractError("findingFingerprintInvalid")
    if len(fingerprints) != len(set(fingerprints)):
        raise EvidenceContractError("findingFingerprintDuplicate")
    ordered = sorted(fingerprints, key=lambda value: value.encode("utf-8"))
    return tuple(
        {
            "eventId": f"{ordinal:032x}",
            "filename": f"{ordinal:032x}.json",
            "fingerprint": fingerprint,
        }
        for ordinal, fingerprint in enumerate(ordered, start=1)
    )


def validate_finding_event_file(payload: bytes) -> dict:
    """Validate one canonical privacy-safe finding event record file."""

    document = _load_canonical_file(payload)
    _validate_finding_event_record(document)
    return document


def validate_finding_event_records(records: Sequence[Mapping[str, object]]) -> tuple:
    """Validate one run's complete occurrence, context, and family record groups."""

    if not isinstance(records, (list, tuple)):
        raise EvidenceContractError("findingEventRecordsInvalid")
    normalized = tuple(
        dict(record) if isinstance(record, Mapping) else record
        for record in records
    )
    for record in normalized:
        _validate_finding_event_record(record)
    _validate_finding_event_groups(normalized)
    return normalized


def _validate_finding_event_record(record: object) -> None:
    if not isinstance(record, Mapping) or set(record) != _FINDING_EVENT_FIELDS:
        raise EvidenceContractError("findingEventFieldsInvalid")
    _require_member(record["event"], _FINDING_EVENTS, "findingEventEventInvalid")
    _require_member(
        record["findingClass"],
        _FINDING_CLASSES,
        "findingEventClassInvalid",
    )
    _require_safe_code(record["defectKind"], "findingEventDefectKindInvalid")
    _require_safe_code(
        record["diagnosticCode"],
        "findingEventDiagnosticCodeInvalid",
    )
    _require_hex(record["findingToken"], "findingEventTokenInvalid")
    _require_member(
        record["fingerprintKind"],
        _FINGERPRINT_KINDS,
        "findingEventFingerprintKindInvalid",
    )
    if not isinstance(record["fingerprintVersion"], str):
        raise EvidenceContractError("findingEventFingerprintVersionInvalid")
    _require_hex(record["value"], "findingEventFingerprintValueInvalid")
    if record["observationSource"] != "fresh":
        raise EvidenceContractError("findingEventObservationSourceInvalid")


def _require_member(value: object, allowed: set, code: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise EvidenceContractError(code)
    return value


def _require_safe_code(value: object, code: str) -> str:
    if not isinstance(value, str) or _SAFE_CODE.fullmatch(value) is None:
        raise EvidenceContractError(code)
    return value


def _validate_finding_event_groups(records: Sequence[Mapping[str, object]]) -> None:
    grouped = {}
    for record in records:
        grouped.setdefault(record["findingToken"], []).append(record)
    for group in grouped.values():
        identities = {
            (
                record["findingClass"],
                record["defectKind"],
                record["diagnosticCode"],
            )
            for record in group
        }
        if len(identities) != 1:
            raise EvidenceContractError("findingTokenCollision")
        kinds = [record["fingerprintKind"] for record in group]
        if len(kinds) != len(set(kinds)):
            raise EvidenceContractError("findingFingerprintKindDuplicate")
        if set(kinds) != _FINGERPRINT_KINDS:
            raise EvidenceContractError("findingFingerprintKindsMissing")


def validate_project_state_file(payload: bytes) -> dict:
    """Validate canonical project.json bytes and return the logical document."""

    document = _load_canonical_file(payload)
    _validate_project_state_document(document)
    return document


def project_state_hmac(project_state: Mapping[str, object]) -> str:
    """Bind evidence to the immutable private project identity across key rotation."""

    identifier, _, cleanup_key = _validate_project_state_document(
        project_state
    )
    return hmac.new(
        cleanup_key,
        _PROJECT_STATE_DOMAIN + identifier,
        hashlib.sha256,
    ).hexdigest()


def build_commit_sequence_file(last_allocated: str, cleanup_key: bytes) -> bytes:
    """Create exact authenticated commit-sequence.json bytes."""

    _parse_uint64(last_allocated, allow_zero=False, code="commitSequenceInvalid")
    body = {"lastAllocated": last_allocated, "version": "commit-sequence-v1"}
    record = {
        "hmacSha256": _record_hmac(
            cleanup_key,
            _SEQUENCE_KEY_DOMAIN,
            _SEQUENCE_MAC_DOMAIN,
            body,
        ),
        **body,
    }
    return canonical_json_bytes(record) + b"\n"


def validate_commit_sequence_file(payload: bytes, cleanup_key: bytes) -> int:
    """Authenticate canonical commit-sequence.json bytes."""

    document = _load_canonical_file(payload)
    fields = {"hmacSha256", "lastAllocated", "version"}
    if not isinstance(document, dict) or set(document) != fields:
        raise EvidenceContractError("commitSequenceFieldsInvalid")
    if document["version"] != "commit-sequence-v1":
        raise EvidenceContractError("commitSequenceVersionInvalid")
    value = _parse_uint64(
        document["lastAllocated"],
        allow_zero=False,
        code="commitSequenceInvalid",
    )
    _require_hex(document["hmacSha256"], "commitSequenceHmacInvalid")
    body = {"lastAllocated": document["lastAllocated"], "version": document["version"]}
    expected = _record_hmac(cleanup_key, _SEQUENCE_KEY_DOMAIN, _SEQUENCE_MAC_DOMAIN, body)
    if not hmac.compare_digest(document["hmacSha256"], expected):
        raise EvidenceContractError("commitSequenceHmacMismatch")
    return value


def validate_commit_sequence_state(
    sequence_payload: Optional[bytes],
    cleanup_key: bytes,
    completed_sequences: Sequence[str],
    retention_high_waters: Sequence[str],
) -> int:
    """Reject duplicate or rolled-back commit sequence state while allowing gaps."""

    completed = _sequence_values(
        completed_sequences,
        allow_zero=False,
        code="evidenceCommitSequenceInvalid",
    )
    if len(completed) != len(set(completed)):
        raise EvidenceContractError("commitSequenceDuplicate")
    retention = _sequence_values(
        retention_high_waters,
        allow_zero=True,
        code="retentionHighWaterInvalid",
    )
    floor = max(completed + retention, default=0)
    if sequence_payload is None:
        if floor:
            raise EvidenceContractError("commitSequenceMissing")
        return 0
    current = validate_commit_sequence_file(sequence_payload, cleanup_key)
    if current < floor:
        raise EvidenceContractError("commitSequenceRollback")
    return current


def build_evidence_file(body: Mapping[str, object], project_state: Mapping[str, object]) -> bytes:
    """Validate and authenticate one terminal evidence body."""

    _validate_evidence_body(body, project_state, allow_historical_epoch=False)
    _, _, cleanup_key = _project_keys(project_state)
    record = dict(body)
    record["hmacSha256"] = _record_hmac(
        cleanup_key,
        _EVIDENCE_KEY_DOMAIN,
        _EVIDENCE_MAC_DOMAIN,
        body,
    )
    return canonical_json_bytes(record) + b"\n"


def validate_evidence_file(payload: bytes, project_state: Mapping[str, object]) -> dict:
    """Authenticate exact evidence.json bytes and validate cross-field semantics."""

    document = _load_canonical_file(payload)
    _, _, cleanup_key = _validate_project_state_document(project_state)
    expected_fields = _EVIDENCE_BODY_FIELDS | {"hmacSha256"}
    if not isinstance(document, dict) or set(document) != expected_fields:
        raise EvidenceContractError("evidenceFieldsInvalid")
    _require_hex(document["hmacSha256"], "evidenceHmacInvalid")
    body = {name: value for name, value in document.items() if name != "hmacSha256"}
    expected = _record_hmac(cleanup_key, _EVIDENCE_KEY_DOMAIN, _EVIDENCE_MAC_DOMAIN, body)
    if not hmac.compare_digest(document["hmacSha256"], expected):
        raise EvidenceContractError("evidenceHmacMismatch")
    _validate_evidence_body(body, project_state, allow_historical_epoch=True)
    return document


def _encode_json(value: object) -> bytes:
    if value is None:
        return b"null"
    if type(value) is bool:
        return b"true" if value else b"false"
    if type(value) is int:
        return _encode_integer(value)
    if isinstance(value, str):
        return _encode_string(value)
    if isinstance(value, list):
        return b"[" + b",".join(_encode_json(item) for item in value) + b"]"
    if isinstance(value, dict):
        return _encode_object(value)
    raise EvidenceContractError("canonicalJsonTypeInvalid")


def _encode_integer(value: int) -> bytes:
    if value < 0 or value > MAX_SAFE_INTEGER:
        raise EvidenceContractError("canonicalJsonIntegerOutOfRange")
    return str(value).encode("ascii")


def _encode_string(value: str) -> bytes:
    output = bytearray(b'"')
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise EvidenceContractError("canonicalJsonUnicodeScalarInvalid")
        if character in ('"', "\\"):
            output.extend(b"\\" + character.encode("ascii"))
        elif codepoint <= 0x1F:
            output.extend(("\\u%04x" % codepoint).encode("ascii"))
        else:
            output.extend(character.encode("utf-8"))
    output.extend(b'"')
    return bytes(output)


def _encode_object(value: dict) -> bytes:
    if any(not isinstance(name, str) for name in value):
        raise EvidenceContractError("canonicalJsonKeyInvalid")
    try:
        names = sorted(value, key=lambda name: name.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise EvidenceContractError("canonicalJsonUnicodeScalarInvalid") from error
    fields = (_encode_string(name) + b":" + _encode_json(value[name]) for name in names)
    return b"{" + b",".join(fields) + b"}"


def _load_canonical_file(payload: bytes) -> dict:
    if not isinstance(payload, bytes):
        raise EvidenceContractError("jsonBytesRequired")
    try:
        document = load_contract_json_bytes(payload)
    except ContractJsonError as error:
        raise EvidenceContractError(error.code) from error
    if payload != canonical_json_bytes(document) + b"\n":
        raise EvidenceContractError("canonicalJsonMismatch")
    return document


def _project_keys(project_state: Mapping[str, object]) -> Tuple[bytes, bytes, bytes]:
    if not isinstance(project_state, Mapping):
        raise EvidenceContractError("projectStateFieldsInvalid")
    identifier = _decode_base64url(project_state.get("projectIdentifier"), 16)
    fingerprint_key = _decode_base64url(project_state.get("fingerprintHmacKey"), 32)
    cleanup_key = _decode_base64url(project_state.get("cleanupLeaseKey"), 32)
    return identifier, fingerprint_key, cleanup_key


def _validate_project_state_document(
    document: object,
) -> Tuple[bytes, bytes, bytes]:
    if not isinstance(document, Mapping) or set(document) != _PROJECT_FIELDS:
        raise EvidenceContractError("projectStateFieldsInvalid")
    if document["schemaVersion"] != "sentinel-project-state-v1":
        raise EvidenceContractError("projectStateSchemaVersionInvalid")
    if document["stateVersion"] != "state-v1":
        raise EvidenceContractError("projectStateVersionInvalid")
    _validate_safe_positive_integer(document["keyEpoch"], "keyEpochInvalid")
    identifier, fingerprint_key, cleanup_key = _project_keys(document)
    if hmac.compare_digest(fingerprint_key, cleanup_key):
        raise EvidenceContractError("projectStateKeysNotSeparated")
    return identifier, fingerprint_key, cleanup_key


def _decode_base64url(value: object, size: int) -> bytes:
    if not isinstance(value, str) or _BASE64URL.fullmatch(value) is None:
        raise EvidenceContractError("projectStateEncodingInvalid")
    try:
        decoded = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    except (UnicodeError, ValueError) as error:
        raise EvidenceContractError("projectStateEncodingInvalid") from error
    encoded = base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii")
    if len(decoded) != size or encoded != value:
        raise EvidenceContractError("projectStateEncodingInvalid")
    return decoded


def _validate_safe_positive_integer(value: object, code: str) -> int:
    if type(value) is not int or not 1 <= value <= MAX_SAFE_INTEGER:
        raise EvidenceContractError(code)
    return value


def _parse_uint64(value: object, *, allow_zero: bool, code: str) -> int:
    pattern = _UINT64_ZERO if allow_zero else _UINT64
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise EvidenceContractError(code)
    parsed = int(value)
    if parsed > MAX_UINT64:
        raise EvidenceContractError(code)
    return parsed


def _sequence_values(values: Sequence[str], *, allow_zero: bool, code: str) -> list:
    if not isinstance(values, (list, tuple)):
        raise EvidenceContractError(code)
    return [_parse_uint64(value, allow_zero=allow_zero, code=code) for value in values]


def _record_hmac(
    key: bytes,
    key_domain: bytes,
    mac_domain: bytes,
    body: Mapping[str, object],
) -> str:
    if not isinstance(key, bytes) or len(key) != 32:
        raise EvidenceContractError("cleanupLeaseKeyInvalid")
    derived_key = hmac.new(key, key_domain, hashlib.sha256).digest()
    mac_input = mac_domain + canonical_json_bytes(dict(body))
    return hmac.new(derived_key, mac_input, hashlib.sha256).hexdigest()


def _require_hex(value: object, code: str) -> str:
    if not isinstance(value, str) or _HEX_256.fullmatch(value) is None:
        raise EvidenceContractError(code)
    return value


def _validate_evidence_body(
    body: Mapping[str, object],
    project_state: Mapping[str, object],
    *,
    allow_historical_epoch: bool,
) -> None:
    if not isinstance(body, Mapping) or set(body) != _EVIDENCE_BODY_FIELDS:
        raise EvidenceContractError("evidenceFieldsInvalid")
    _validate_evidence_identity(body)
    _validate_evidence_times(body)
    passes = _validate_components(body["command"], body["components"])
    _validate_terminal(body, passes)
    _validate_manifest(body)
    _validate_diagnostics(body["diagnosticCodes"])
    _validate_evidence_project_binding(
        body,
        project_state,
        allow_historical_epoch=allow_historical_epoch,
    )


def _validate_evidence_identity(body: Mapping[str, object]) -> None:
    if body["schemaVersion"] != "sentinel-evidence-v1":
        raise EvidenceContractError("evidenceSchemaVersionInvalid")
    if not isinstance(body["specVersion"], str) or _SEMVER.fullmatch(body["specVersion"]) is None:
        raise EvidenceContractError("specVersionInvalid")
    if body["fingerprintVersion"] != "sentinel-fingerprint-v1":
        raise EvidenceContractError("fingerprintVersionInvalid")
    _validate_uuid(body["runId"], "runIdInvalid")
    _validate_uuid(body["correlationId"], "correlationIdInvalid")
    if body["command"] not in {"crap", "mutation", "check"}:
        raise EvidenceContractError("commandInvalid")
    if body["language"] not in {"python", "typescript", "go", "java", "clojure"}:
        raise EvidenceContractError("languageInvalid")
    if body["mode"] not in {"strict", "local"}:
        raise EvidenceContractError("modeInvalid")
    if body["observationSource"] not in {"fresh", "cache"}:
        raise EvidenceContractError("observationSourceInvalid")
    _parse_uint64(body["commitSequence"], allow_zero=False, code="commitSequenceInvalid")
    _validate_safe_positive_integer(body["keyEpoch"], "keyEpochInvalid")
    _require_hex(body["projectStateHmac"], "projectStateHmacInvalid")
    _require_hex(body["startedSha256"], "startedSha256Invalid")
    _validate_source_run(body)
    if body["mode"] == "strict" and body["observationSource"] == "cache":
        raise EvidenceContractError("strictCacheInvalid")


def _validate_uuid(value: object, code: str) -> str:
    if not isinstance(value, str) or _UUID.fullmatch(value) is None:
        raise EvidenceContractError(code)
    try:
        canonical = str(uuid.UUID(value))
    except ValueError as error:
        raise EvidenceContractError(code) from error
    if canonical != value:
        raise EvidenceContractError(code)
    return value


def _validate_source_run(body: Mapping[str, object]) -> None:
    source = body["sourceRunId"]
    if body["observationSource"] == "fresh":
        if source is not None:
            raise EvidenceContractError("sourceRunIdInvalid")
        return
    _validate_uuid(source, "sourceRunIdInvalid")
    if source == body["runId"]:
        raise EvidenceContractError("sourceRunIdInvalid")


def _validate_evidence_times(body: Mapping[str, object]) -> None:
    started = _timestamp_key(body["startedAtUtc"])
    completed = _timestamp_key(body["completedAtUtc"])
    committed = _timestamp_key(body["committedAtUtc"])
    if not started <= completed <= committed:
        raise EvidenceContractError("evidenceTimeOrderInvalid")


def _timestamp_key(value: object) -> tuple:
    if not isinstance(value, str):
        raise EvidenceContractError("utcTimestampInvalid")
    match = _UTC.fullmatch(value)
    if match is None or (match.group(7) is not None and match.group(7).endswith("0")):
        raise EvidenceContractError("utcTimestampInvalid")
    parts = [int(item) for item in match.groups()[:6]]
    try:
        instant = datetime(*parts)
    except ValueError as error:
        raise EvidenceContractError("utcTimestampInvalid") from error
    nanos = int((match.group(7) or "0").ljust(9, "0"))
    return calendar.timegm(instant.timetuple()), nanos


def _validate_components(command: str, components: object) -> bool:
    if not isinstance(components, dict):
        raise EvidenceContractError("evidenceComponentsInvalid")
    required = {"crap", "mutation"} if command == "check" else {command}
    if set(components) != required:
        raise EvidenceContractError("evidenceComponentsInvalid")
    if "crap" in components:
        _validate_crap_component(components["crap"])
    if "mutation" in components:
        _validate_mutation_component(components["mutation"])
    return all(component["pass"] for component in components.values())


def _validate_crap_component(component: object) -> None:
    if not isinstance(component, dict) or set(component) != _CRAP_FIELDS:
        raise EvidenceContractError("crapComponentInvalid")
    numerator = _decimal_text(
        component["maxNumerator"],
        allow_zero=True,
        max_length=96,
        code="crapComponentInvalid",
    )
    denominator = _decimal_text(
        component["maxDenominator"],
        allow_zero=False,
        max_length=48,
        code="crapComponentInvalid",
    )
    if math.gcd(numerator, denominator) != 1:
        raise EvidenceContractError("crapComponentFractionInvalid")
    callable_count = component["callableCount"]
    unknown = component["unknownCount"]
    if (
        type(callable_count) is not int
        or not 0 <= callable_count <= MAX_SAFE_INTEGER
        or type(unknown) is not int
        or not 0 <= unknown <= callable_count
        or type(component["pass"]) is not bool
    ):
        raise EvidenceContractError("crapComponentInvalid")
    has_no_known_callable = callable_count == unknown
    if has_no_known_callable != (numerator == 0 and denominator == 1):
        raise EvidenceContractError("crapComponentInventoryInvalid")
    expected = (
        callable_count > 0
        and unknown == 0
        and numerator <= 8 * denominator
    )
    if component["pass"] != expected:
        raise EvidenceContractError("crapComponentSemanticsInvalid")


def _decimal_text(
    value: object,
    *,
    allow_zero: bool,
    max_length: int,
    code: str,
) -> int:
    pattern = _UINT64_ZERO if allow_zero else _UINT64
    if (
        not isinstance(value, str)
        or len(value) > max_length
        or pattern.fullmatch(value) is None
    ):
        raise EvidenceContractError(code)
    return int(value)


def _validate_mutation_component(component: object) -> None:
    if (
        not isinstance(component, dict)
        or set(component) != _MUTATION_FIELDS
        or type(component["pass"]) is not bool
    ):
        raise EvidenceContractError("mutationComponentInvalid")
    counts = {state: component[state] for state in MUTATION_STATES}
    try:
        result = evaluate_mutation(
            counts,
            component["inScope"],
            component["unauthorizedExclusion"],
        )
    except MutationInputError as error:
        raise EvidenceContractError("mutationComponentInvalid") from error
    if component["pass"] != result.passed:
        raise EvidenceContractError("mutationComponentSemanticsInvalid")


def _validate_terminal(body: Mapping[str, object], components_pass: bool) -> None:
    status = body["terminalStatus"]
    if status not in _TERMINAL_EXIT or body["exitCode"] != _TERMINAL_EXIT[status]:
        raise EvidenceContractError("terminalStatusExitCodeMismatch")
    mutation = body["components"].get("mutation")
    if mutation is not None and mutation["toolError"] > 0 and status != "backendError":
        raise EvidenceContractError("terminalStatusPrecedenceInvalid")
    if status == "passed" and not components_pass:
        raise EvidenceContractError("terminalComponentMismatch")
    if status == "qualityFailed" and components_pass:
        raise EvidenceContractError("terminalComponentMismatch")
    certified = (
        body["mode"] == "strict"
        and body["observationSource"] == "fresh"
        and status == "passed"
        and components_pass
    )
    if type(body["certification"]) is not bool or body["certification"] != certified:
        raise EvidenceContractError("certificationInvalid")


def _validate_manifest(body: Mapping[str, object]) -> None:
    count = body["eventCount"]
    events = body["events"]
    if (
        type(count) is not int
        or not 0 <= count <= MAX_SAFE_INTEGER
        or not isinstance(events, list)
    ):
        raise EvidenceContractError("eventManifestInvalid")
    if count != len(events):
        raise EvidenceContractError("eventManifestCountMismatch")
    names = [_validate_manifest_entry(entry) for entry in events]
    if len(names) != len(set(names)):
        raise EvidenceContractError("eventManifestDuplicate")
    expected = [f"{index:032x}.json" for index in range(1, len(names) + 1)]
    if names != expected:
        raise EvidenceContractError("eventManifestOrdinalInvalid")
    if body["observationSource"] == "cache" and events:
        raise EvidenceContractError("cacheObservationHasEvents")


def _validate_manifest_entry(entry: object) -> str:
    if not isinstance(entry, dict) or set(entry) != {"filename", "sha256"}:
        raise EvidenceContractError("eventManifestInvalid")
    if (
        not isinstance(entry["filename"], str)
        or _EVENT_FILENAME.fullmatch(entry["filename"]) is None
    ):
        raise EvidenceContractError("eventManifestFilenameInvalid")
    _require_hex(entry["sha256"], "eventManifestDigestInvalid")
    return entry["filename"]


def _validate_diagnostics(value: object) -> None:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or _SAFE_CODE.fullmatch(item) is None
        for item in value
    ):
        raise EvidenceContractError("diagnosticCodesInvalid")
    ordered = sorted(value, key=lambda item: item.encode("utf-8"))
    if len(value) != len(set(value)) or value != ordered:
        raise EvidenceContractError("diagnosticCodesInvalid")


def _validate_evidence_project_binding(
    body: Mapping[str, object],
    project_state: Mapping[str, object],
    *,
    allow_historical_epoch: bool,
) -> None:
    expected_hmac = project_state_hmac(project_state)
    epoch = project_state["keyEpoch"]
    if body["keyEpoch"] > epoch or (
        not allow_historical_epoch and body["keyEpoch"] != epoch
    ):
        raise EvidenceContractError("keyEpochInvalid")
    if not hmac.compare_digest(body["projectStateHmac"], expected_hmac):
        raise EvidenceContractError("projectStateBindingInvalid")
