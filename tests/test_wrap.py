"""Tests for nass.wrap."""

from __future__ import annotations

import pytest

import nass


def test_wrap_basic() -> None:
    assert nass.wrap("مرحبا بالعالم", 12) == ["مرحبا", "بالعالم"]


def test_wrap_uses_the_measurer() -> None:
    lines = nass.wrap("مرحبا بالعالم", 12, measure=lambda s: len(s) * 2)
    assert lines == ["مرحبا", "بالعالم"]


def test_wrap_never_starts_a_line_with_punctuation() -> None:
    lines = nass.wrap("مرحبا ، بالعالم", 8)
    assert lines == ["مرحبا ،", "بالعالم"]
    assert all(not line.startswith("،") for line in lines)


def test_wrap_keeps_opening_bracket_with_next_word() -> None:
    lines = nass.wrap("قال ( مرحبا ) ثم ذهب", 10)
    assert all(not line.endswith("(") for line in lines)


def test_wrap_empty() -> None:
    assert nass.wrap("", 10) == []
    assert nass.wrap("   ", 10) == []


def test_wrap_rejects_bad_width() -> None:
    with pytest.raises(ValueError):
        nass.wrap("x", 0)
    with pytest.raises(ValueError):
        nass.wrap("x", -1)


def test_wrap_does_not_split_long_words_by_default() -> None:
    assert nass.wrap("abcdefghij", 3) == ["abcdefghij"]


def test_wrap_splits_long_words_when_asked() -> None:
    assert nass.wrap("abcdefghij", 3, break_long_words=True) == [
        "abc",
        "def",
        "ghi",
        "j",
    ]


def test_wrap_single_word_fits() -> None:
    assert nass.wrap("مرحبا", 10) == ["مرحبا"]


def test_wrap_preserves_all_words() -> None:
    text = "هذا نص عربي طويل إلى حد ما لاختبار تقسيم الأسطر"
    lines = nass.wrap(text, 20)
    assert " ".join(lines) == text
