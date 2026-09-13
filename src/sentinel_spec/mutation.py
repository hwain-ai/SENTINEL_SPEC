"""Exact mutation state validation and killed-only gate contract."""

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional

from .threshold import DEFAULT_MUTATION_MIN, parse_mutation_min


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
MAX_SAFE_INTEGER = 9_007_199_254_740_991


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
    if value < 0 or value > MAX_SAFE_INTEGER:
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


def evaluate_mutation(
    counts,
    in_scope,
    unauthorized_exclusion=0,
    mutation_min=DEFAULT_MUTATION_MIN,
):
    """Validate all counts and return the minimum-kill-rate gate result.

    The default minimum of 100 percent is the killed-only gate: every in-scope
    mutant must be killed, so no other state can remain.
    """

    minimum = parse_mutation_min(mutation_min)
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
    # 100 percent means killed == in_scope, which forces every other state to zero.
    passed = (
        in_scope >= 1
        and unauthorized_exclusion == 0
        and killed * 100 * minimum.denominator >= minimum.numerator * in_scope
    )
    return MutationResult(
        in_scope=in_scope,
        killed=killed,
        unauthorized_exclusion=unauthorized_exclusion,
        kill_rate=kill_rate,
        passed=passed,
    )
