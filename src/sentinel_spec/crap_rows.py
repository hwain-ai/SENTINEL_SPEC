"""Language-neutral validation and ordering for callable CRAP rows."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cmp_to_key
from pathlib import PurePosixPath
from typing import Iterable, Optional, Tuple


MAX_SAFE_INTEGER = 9_007_199_254_740_991


class CrapRowError(ValueError):
    """Raised when a row cannot participate in the exact total order."""


@dataclass(frozen=True)
class CrapRow:
    module_relative_path: str
    source_start_byte: int
    callable_id: str
    numerator: Optional[int]
    denominator: Optional[int]
    unknown_reason: Optional[str]

    def __post_init__(self) -> None:
        _validate_identity(
            self.module_relative_path,
            self.source_start_byte,
            self.callable_id,
        )
        if self.unknown_reason is None:
            _require_integer("numerator", self.numerator, minimum=0)
            _require_integer("denominator", self.denominator, minimum=1)
            if math.gcd(self.numerator, self.denominator) != 1:
                raise CrapRowError("fractionNotReduced")
            return
        if not isinstance(self.unknown_reason, str) or not self.unknown_reason:
            raise CrapRowError("unknownReasonMissing")
        _utf8_bytes("unknown_reason", self.unknown_reason)
        if self.numerator is not None or self.denominator is not None:
            raise CrapRowError("unknownFractionPresent")

    @classmethod
    def known(
        cls,
        module_relative_path: str,
        source_start_byte: int,
        callable_id: str,
        numerator: int,
        denominator: int,
    ) -> "CrapRow":
        return cls(
            module_relative_path=module_relative_path,
            source_start_byte=source_start_byte,
            callable_id=callable_id,
            numerator=numerator,
            denominator=denominator,
            unknown_reason=None,
        )

    @classmethod
    def unknown(
        cls,
        module_relative_path: str,
        source_start_byte: int,
        callable_id: str,
        unknown_reason: str,
    ) -> "CrapRow":
        return cls(
            module_relative_path=module_relative_path,
            source_start_byte=source_start_byte,
            callable_id=callable_id,
            numerator=None,
            denominator=None,
            unknown_reason=unknown_reason,
        )

    @property
    def is_unknown(self) -> bool:
        return self.unknown_reason is not None


def sort_crap_rows(rows: Iterable[CrapRow]) -> Tuple[CrapRow, ...]:
    """Return the strict CRAP report order without modifying caller data."""

    materialized = tuple(rows)
    seen = set()
    for row in materialized:
        if not isinstance(row, CrapRow):
            raise CrapRowError("rowTypeInvalid")
        identity_key = (
            _utf8_bytes("module_relative_path", row.module_relative_path),
            row.source_start_byte,
            _utf8_bytes("callable_id", row.callable_id),
        )
        if identity_key in seen:
            raise CrapRowError("identityAmbiguous")
        seen.add(identity_key)
    return tuple(sorted(materialized, key=cmp_to_key(_compare_rows)))


def _compare_rows(left: CrapRow, right: CrapRow) -> int:
    if left.is_unknown != right.is_unknown:
        return -1 if left.is_unknown else 1
    if not left.is_unknown:
        left_numerator = _known_integer(left.numerator)
        left_denominator = _known_integer(left.denominator)
        right_numerator = _known_integer(right.numerator)
        right_denominator = _known_integer(right.denominator)
        comparison = left_numerator * right_denominator - right_numerator * left_denominator
        if comparison:
            return -1 if comparison > 0 else 1

    left_identity = _identity_sort_key(left)
    right_identity = _identity_sort_key(right)
    return (left_identity > right_identity) - (left_identity < right_identity)


def _identity_sort_key(row: CrapRow):
    return (
        _utf8_bytes("module_relative_path", row.module_relative_path),
        row.source_start_byte,
        _utf8_bytes("callable_id", row.callable_id),
    )


def _validate_identity(module_relative_path: str, source_start_byte: int, callable_id: str) -> None:
    _validate_module_path(module_relative_path)
    _validate_source_start_byte(source_start_byte)
    _validate_callable_id(callable_id)


def _validate_module_path(module_relative_path: str) -> None:
    path_bytes = _utf8_bytes("module_relative_path", module_relative_path)
    if not path_bytes or b"\\" in path_bytes or b"\x00" in path_bytes:
        raise CrapRowError("modulePathInvalid")
    _validate_module_path_structure(module_relative_path)


def _validate_module_path_structure(module_relative_path: str) -> None:
    path = PurePosixPath(module_relative_path)
    if (
        path.is_absolute()
        or str(path) != module_relative_path
        or not path.parts
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise CrapRowError("modulePathInvalid")


def _validate_source_start_byte(source_start_byte: int) -> None:
    if not isinstance(source_start_byte, int) or isinstance(source_start_byte, bool):
        raise CrapRowError("sourceStartByteInvalid")
    if source_start_byte < 0:
        raise CrapRowError("sourceStartByteInvalid")
    if source_start_byte > MAX_SAFE_INTEGER:
        raise CrapRowError("sourceStartByteInvalid")


def _validate_callable_id(callable_id: str) -> None:
    if not isinstance(callable_id, str) or not callable_id:
        raise CrapRowError("callableIdInvalid")
    _utf8_bytes("callable_id", callable_id)


def _utf8_bytes(name: str, value: str) -> bytes:
    if not isinstance(value, str):
        raise CrapRowError(f"{name}TypeInvalid")
    try:
        return value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise CrapRowError(f"{name}Utf8Invalid") from error


def _require_integer(name: str, value: Optional[int], minimum: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise CrapRowError(f"{name}Invalid")


def _known_integer(value: Optional[int]) -> int:
    if value is None:
        raise CrapRowError("knownFractionMissing")
    return value
