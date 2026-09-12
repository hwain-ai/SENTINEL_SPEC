"""Raw JSON boundary shared by executable SENTINEL contracts."""

from __future__ import annotations

import json
import re
from typing import Any


_MAX_SAFE_INTEGER_TEXT = "9007199254740991"
_CANONICAL_INTEGER = re.compile(r"-?(?:0|[1-9][0-9]*)")


class ContractJsonError(ValueError):
    """Raised when raw JSON cannot be converted without contract data loss."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def load_contract_json_bytes(payload: bytes) -> Any:
    """Decode canonical integer-only JSON without losing object or number data."""

    if not isinstance(payload, bytes):
        raise ContractJsonError("jsonBytesRequired")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractJsonError("jsonUtf8Invalid") from error
    if text.startswith("\ufeff"):
        raise ContractJsonError("jsonBomForbidden")
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_int=_parse_integer,
            parse_float=_reject_noninteger_number,
            parse_constant=_reject_noninteger_number,
        )
    except ContractJsonError:
        raise
    except json.JSONDecodeError as error:
        raise ContractJsonError("jsonSyntaxInvalid") from error


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractJsonError("jsonDuplicateKey")
        result[key] = value
    return result


def _parse_integer(token: str) -> int:
    if _CANONICAL_INTEGER.fullmatch(token) is None or token == "-0":
        raise ContractJsonError("jsonIntegerLexemeInvalid")
    magnitude = token[1:] if token.startswith("-") else token
    if len(magnitude) > len(_MAX_SAFE_INTEGER_TEXT):
        raise ContractJsonError("jsonIntegerOutOfRange")
    if len(magnitude) == len(_MAX_SAFE_INTEGER_TEXT):
        if magnitude > _MAX_SAFE_INTEGER_TEXT:
            raise ContractJsonError("jsonIntegerOutOfRange")
    return int(token)


def _reject_noninteger_number(_token: str):
    raise ContractJsonError("jsonIntegerLexemeInvalid")
