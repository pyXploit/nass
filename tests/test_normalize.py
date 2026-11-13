"""Tests for nass.normalize."""

from __future__ import annotations

import pytest

import nass


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("أحمد", "احمد"),
        ("إبراهيم", "ابراهيم"),
        ("آمن", "امن"),
        ("ٱلله", "الله"),
        ("مدرسة", "مدرسه"),
        ("مصطفى", "مصطفي"),
        ("كـتـاب", "كتاب"),
        ("مُحَمَّد", "محمد"),
        ("١٢٣", "123"),
        ("۱۲۳", "123"),
        ("", ""),
    ],
)
def test_normalize_defaults(raw: str, expected: str) -> None:
    assert nass.normalize(raw) == expected


def test_normalize_keeps_diacritics_when_asked() -> None:
    assert nass.normalize("مُحَمَّد", strip_diacritics=False) == "مُحَمَّد"


def test_normalize_keeps_teh_marbuta_when_asked() -> None:
    assert nass.normalize("مدرسة", unify_teh_marbuta=False) == "مدرسة"


def test_normalize_keeps_alef_when_asked() -> None:
    assert nass.normalize("أحمد", unify_alef=False) == "أحمد"


def test_normalize_keeps_tatweel_when_asked() -> None:
    assert nass.normalize("كـتاب", strip_tatweel=False) == "كـتاب"


def test_normalize_keeps_digits_when_asked() -> None:
    assert nass.normalize("١٢٣", unify_digits=False) == "١٢٣"


@pytest.mark.parametrize("text", ["أحمد", "مُحَمَّد", "١٢٣", "hello", "مدرسة أحمد"])
def test_normalize_is_idempotent(text: str) -> None:
    once = nass.normalize(text)
    assert nass.normalize(once) == once


def test_normalize_leaves_latin_alone() -> None:
    assert nass.normalize("Hello, world!") == "Hello, world!"


def test_remove_diacritics() -> None:
    assert nass.remove_diacritics("مُحَمَّدٌ") == "محمد"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("مرحبا", True),
        ("hello", False),
        ("", False),
        ("12345", False),
        ("مرحبا بالعالم hello", True),
        ("hello world مرحبا", False),
    ],
)
def test_is_arabic(text: str, expected: bool) -> None:
    assert nass.is_arabic(text) is expected


def test_is_arabic_threshold() -> None:
    mixed = "hello مرحبا"
    assert nass.is_arabic(mixed, threshold=0.3) is True
    assert nass.is_arabic(mixed, threshold=0.9) is False


def test_collapse_whitespace() -> None:
    assert nass.collapse_whitespace("  a \n\t b  ") == "a b"
    assert nass.collapse_whitespace("   ") == ""
