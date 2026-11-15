"""The API reference is executable: every example must produce what it claims."""

from __future__ import annotations

import doctest
from pathlib import Path

import nass
from nass import inflect

DOC = Path(__file__).resolve().parent.parent / "docs" / "api.md"


def test_api_reference_examples() -> None:
    result = doctest.testfile(
        str(DOC),
        module_relative=False,
        globs={"nass": nass, "inflect": inflect},
    )
    assert result.attempted > 0, "no examples found in docs/api.md"
    assert result.failed == 0, f"{result.failed} of {result.attempted} examples failed"
