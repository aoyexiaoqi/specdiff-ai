"""Key-parameter extraction from clause text.

Deterministic, regex-based extraction of the numeric parameters that carry
engineering meaning inside a technical-agreement clause:

* plain values with units   -- ``8.5 kA``, ``6.0 mm``, ``300 ℃``
* tolerances                -- ``±0.2 kN``, ``±0.5 mm``
* ranges                    -- ``5~10 mm``, ``20-30 ℃``
* percentages               -- ``5 %``, ``95%``

The extractor is deliberately conservative: a bare number without a unit,
a ``%`` sign, a ``±`` sign or a range separator is *not* treated as a
parameter, so clause numbers (``3.2.1``), years (``2024``) and season
markers (``S01-S05``) do not produce false positives.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Units recognised after a number.  Longer units come first in the regex
# alternation so that e.g. ``mm`` wins over ``m`` and ``kA`` over ``A``.
UNITS = [
    "N·m", "r/min", "L/min",
    "℃", "°C", "μm", "um", "mm", "cm",
    "MPa", "GPa", "kPa", "Pa",
    "kN", "N", "kA", "mA", "A", "kV", "V",
    "Hz", "kHz", "rpm",
    "HRC", "HB", "HV", "Ra",
    "kg", "g", "ms", "min", "dB",
    "周波", "m", "s", "h",
]

_NUM = r"\d+(?:\.\d+)?"
_UNIT = "(?:" + "|".join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True)) + ")"

_TOL_RE = re.compile(r"±\s*(" + _NUM + r")\s*(" + _UNIT + r")?")
_RANGE_TILDE_RE = re.compile(
    r"(" + _NUM + r")\s*[~～]\s*(" + _NUM + r")\s*(" + _UNIT + r")?"
)
_RANGE_DASH_RE = re.compile(
    r"(" + _NUM + r")\s*[-–—]\s*(" + _NUM + r")\s*(" + _UNIT + r")"
)
_PCT_RE = re.compile(r"(" + _NUM + r")\s*%")
_VAL_RE = re.compile(r"(" + _NUM + r")\s*(" + _UNIT + r")(?![A-Za-z])")


def _fmt(value: float) -> str:
    """Format a float the way an engineer would write it (``8.5``, ``6``)."""
    return "%g" % value


@dataclass
class Param:
    """One extracted key parameter."""

    kind: str  # "value" | "tolerance" | "range" | "percent"
    unit: str = ""
    value: Optional[float] = None
    low: Optional[float] = None
    high: Optional[float] = None

    @property
    def raw(self) -> str:
        if self.kind == "range":
            text = "%s~%s" % (_fmt(self.low or 0.0), _fmt(self.high or 0.0))
        elif self.kind == "tolerance":
            text = "±" + _fmt(self.value or 0.0)
        elif self.kind == "percent":
            text = _fmt(self.value or 0.0) + "%"
        else:
            text = _fmt(self.value or 0.0)
        if self.unit and self.kind != "percent":
            text += " " + self.unit
        return text

    def signature(self) -> Tuple:
        """Identity used for equality checks between two document versions."""
        if self.kind == "range":
            return (self.kind, self.unit, self.low, self.high)
        return (self.kind, self.unit, self.value)


def extract_params(text: str) -> List[Param]:
    """Extract every key parameter from *text*, in order of appearance."""
    claimed: List[Tuple[int, int]] = []
    found: List[Tuple[int, Param]] = []

    def overlaps(start: int, end: int) -> bool:
        return any(start < c_end and c_start < end for c_start, c_end in claimed)

    def scan(pattern: "re.Pattern[str]", builder) -> None:
        for match in pattern.finditer(text):
            start, end = match.span()
            if overlaps(start, end):
                continue
            claimed.append((start, end))
            found.append((start, builder(match)))

    def _tol(m: "re.Match[str]") -> Param:
        return Param(kind="tolerance", unit=m.group(2) or "", value=float(m.group(1)))

    def _range(m: "re.Match[str]") -> Param:
        return Param(
            kind="range",
            unit=m.group(3) or "",
            low=float(m.group(1)),
            high=float(m.group(2)),
        )

    def _pct(m: "re.Match[str]") -> Param:
        return Param(kind="percent", unit="%", value=float(m.group(1)))

    def _val(m: "re.Match[str]") -> Param:
        return Param(kind="value", unit=m.group(2), value=float(m.group(1)))

    scan(_TOL_RE, _tol)
    scan(_RANGE_TILDE_RE, _range)
    scan(_RANGE_DASH_RE, _range)
    scan(_PCT_RE, _pct)
    scan(_VAL_RE, _val)

    found.sort(key=lambda item: item[0])
    return [param for _, param in found]
