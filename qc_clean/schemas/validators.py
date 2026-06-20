"""Shared schema validators for LLM-facing fields.

Value-level range constraints (``ge``/``le``) are NOT enforced at decode time by
any provider, so an out-of-range LLM value would raise a ``ValidationError`` and
crash the stage. Confidence/strength/score are soft, uncalibrated signals
(see PROJECT_THEORY_AND_GOALS.md §15) — clamping a stray 1.2 -> 1.0 is correct
and robust, where crashing is not. Use ``Confidence01`` instead of
``Field(ge=0.0, le=1.0)`` for 0..1 fields.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BeforeValidator


def _clamp01(value):
    """Coerce to float and clamp into [0.0, 1.0]; non-numeric -> 0.0."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    if f < 0.0:
        return 0.0
    if f > 1.0:
        return 1.0
    return f


# A 0..1 score that clamps out-of-range LLM output instead of raising.
Confidence01 = Annotated[float, BeforeValidator(_clamp01)]
