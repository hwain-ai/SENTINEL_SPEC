"""Exact CRAP formula and decimal rendering contract."""

from fractions import Fraction

from .threshold import DEFAULT_CRAP_MAX, parse_crap_max


_DECIMAL_PLACES = 12
_DECIMAL_SCALE = 10**_DECIMAL_PLACES
_MAX_SAFE_INTEGER = 9_007_199_254_740_991


class CrapInputError(ValueError):
    """An input violates the executable CRAP contract."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require_integer(value, field_name):
    if not isinstance(value, int) or isinstance(value, bool):
        raise CrapInputError(f"{field_name}NotInteger")


def _require_range(value, minimum, field_name):
    if value < minimum or value > _MAX_SAFE_INTEGER:
        raise CrapInputError(f"{field_name}OutOfRange")


def _validate_inputs(cyclomatic_complexity, covered_units, total_units):
    _require_integer(cyclomatic_complexity, "cyclomaticComplexity")
    _require_integer(covered_units, "coveredUnits")
    _require_integer(total_units, "totalUnits")

    _require_range(cyclomatic_complexity, 1, "cyclomaticComplexity")
    _require_range(covered_units, 0, "coveredUnits")
    _require_range(total_units, 1, "totalUnits")
    if covered_units > total_units:
        raise CrapInputError("coveredUnitsExceedTotalUnits")


def calculate_crap(cyclomatic_complexity, covered_units, total_units):
    """Return the reduced, exact CRAP score as a Fraction."""

    _validate_inputs(cyclomatic_complexity, covered_units, total_units)

    denominator = total_units**3
    uncovered_units = total_units - covered_units
    numerator = (
        cyclomatic_complexity**2 * uncovered_units**3
        + cyclomatic_complexity * denominator
    )
    return Fraction(numerator, denominator)


def crap_gate_passes(
    cyclomatic_complexity,
    covered_units,
    total_units,
    crap_max=DEFAULT_CRAP_MAX,
):
    """Return whether the exact CRAP score is at most the exact limit (default 8)."""

    limit = parse_crap_max(crap_max)
    value = calculate_crap(cyclomatic_complexity, covered_units, total_units)
    return value.numerator * limit.denominator <= limit.numerator * value.denominator


def render_canonical_decimal(value):
    """Render a nonnegative Fraction with half-even rounding at 12 places."""

    if not isinstance(value, Fraction):
        raise CrapInputError("fractionNotExact")
    if value < 0:
        raise CrapInputError("fractionMustBeNonnegative")

    scaled_numerator = value.numerator * _DECIMAL_SCALE
    rounded, remainder = divmod(scaled_numerator, value.denominator)
    doubled_remainder = remainder * 2
    if doubled_remainder > value.denominator:
        rounded += 1
    elif doubled_remainder == value.denominator and rounded % 2 == 1:
        rounded += 1

    integer_part, fractional_part = divmod(rounded, _DECIMAL_SCALE)
    if fractional_part == 0:
        return str(integer_part)

    fractional_text = f"{fractional_part:0{_DECIMAL_PLACES}d}".rstrip("0")
    return f"{integer_part}.{fractional_text}"
