"""Gate threshold text contract shared by the CRAP and mutation gates."""

import re
from fractions import Fraction


THRESHOLD_PATTERN = re.compile(r"^(0|[1-9][0-9]*)(\.[0-9]{1,2})?$")
DEFAULT_CRAP_MAX = "8"
DEFAULT_MUTATION_MIN = "100"
_PERCENT_MAXIMUM = Fraction(100)


class ThresholdInputError(ValueError):
    """A gate threshold violates the shared text contract."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def parse_threshold(text, field_name):
    """Return the exact Fraction for a decimal threshold with at most two places."""

    if not isinstance(text, str) or not THRESHOLD_PATTERN.fullmatch(text):
        raise ThresholdInputError(f"{field_name}Invalid")
    return Fraction(text)


def parse_crap_max(text):
    """Return the exact CRAP upper bound; zero is not an admissible bound."""

    value = parse_threshold(text, "crapMax")
    if value <= 0:
        raise ThresholdInputError("crapMaxOutOfRange")
    return value


def parse_mutation_min(text):
    """Return the exact minimum kill rate in percent, between 0 and 100."""

    value = parse_threshold(text, "mutationMin")
    if value > _PERCENT_MAXIMUM:
        raise ThresholdInputError("mutationMinOutOfRange")
    return value
