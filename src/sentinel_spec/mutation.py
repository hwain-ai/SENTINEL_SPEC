"""Exact mutation state validation and killed-only gate contract."""

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional


MUTATION_STATES = (
    "killed",
    "survived",
    "uncovered",
    "timedOut",
    "compileError",
    "runtimeError",
    "pending",
    "ignored",
    "toolError",
)


class MutationInputError(ValueError):
    """An input violates the executable mutation contract."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class MutationResult:
    """The exact kill rate and gate decision for validated counts."""

    in_scope: int
    killed: int
    unauthorized_exclusion: int
    kill_rate: Optional[Fraction]
    passed: bool


def _require_nonnegative_integer(value, field_name):
    if not isinstance(value, int) or isinstance(value, bool):
        raise MutationInputError(f"{field_name}NotInteger")
    if value < 0:
        raise MutationInputError(f"{field_name}OutOfRange")


def _validate_state_keys(counts):
    if not isinstance(counts, Mapping):
        raise MutationInputError("mutationCountsNotObject")

    unknown = [key for key in counts if key not in MUTATION_STATES]
    if unknown:
        raise MutationInputError("unknownMutationState")

    missing = [state for state in MUTATION_STATES if state not in counts]
    if missing:
        raise MutationInputError("missingMutationState")


def evaluate_mutation(counts, in_scope, unauthorized_exclusion=0):
    """Validate all counts and return the killed-only mutation gate result."""

    _validate_state_keys(counts)
    for state in MUTATION_STATES:
        _require_nonnegative_integer(counts[state], "mutationCount")
    _require_nonnegative_integer(in_scope, "inScope")
    _require_nonnegative_integer(
        unauthorized_exclusion, "unauthorizedExclusion"
    )

    if sum(counts[state] for state in MUTATION_STATES) != in_scope:
        raise MutationInputError("stateCountMismatch")

    killed = counts["killed"]
    kill_rate = None if in_scope == 0 else Fraction(killed, in_scope)
    passed = (
        in_scope >= 1
        and killed == in_scope
        and all(counts[state] == 0 for state in MUTATION_STATES[1:])
        and unauthorized_exclusion == 0
    )
    return MutationResult(
        in_scope=in_scope,
        killed=killed,
        unauthorized_exclusion=unauthorized_exclusion,
        kill_rate=kill_rate,
        passed=passed,
    )
