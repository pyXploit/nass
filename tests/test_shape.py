"""Tests for nass.shape."""

from __future__ import annotations

import pytest

import nass


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ب", "\ufe8f"),  # isolated
        ("بب", "\ufe91\ufe90"),  # initial + final
        ("ببب", "\ufe91\ufe92\ufe90"),  # initial + medial + final
        ("ا", "\ufe8d"),  # alef is right-joining: isolated
        ("با", "\ufe91\ufe8e"),  # beh initial, alef final
        ("لا", "\ufefb"),  # lam-alef ligature, isolated
        ("بلا", "\ufe91\ufefc"),  # beh initial, lam-alef final
    ],
)
def test_shape(text: str, expected: str) -> None:
    assert nass.shape(text) == expected


def test_shape_ignores_diacritics_when_joining() -> None:
    # The fatha sits between the two behs and must not break the join.
    assert nass.shape("بَب") == "\ufe91\u064e\ufe90"


def test_shape_leaves_latin_alone() -> None:
    assert nass.shape("hello") == "hello"


def test_shape_leaves_punctuation_alone() -> None:
    assert nass.shape("،") == "،"


def test_shape_empty() -> None:
    assert nass.shape("") == ""


def test_display_reverses_arabic() -> None:
    assert nass.display("بب") == "\ufe90\ufe91"


def test_display_keeps_latin_in_order() -> None:
    out = nass.display("مرحبا hello")
    assert out.startswith("hello ")
    assert out.endswith("\ufee3")


def test_display_empty() -> None:
    assert nass.display("") == ""


def test_display_latin_only_is_unchanged() -> None:
    assert nass.display("hello world") == "hello world"


def test_display_keeps_digits_in_order() -> None:
    out = nass.display("صفحة 123")
    assert "123" in out
