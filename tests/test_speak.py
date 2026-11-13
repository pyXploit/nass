"""Tests for nass.speak."""

from __future__ import annotations

import pytest

import nass


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("12:30", "الثانية عشرة والنصف"),
        ("12:00", "الثانية عشرة تماماً"),
        ("12:15", "الثانية عشرة والربع"),
        ("12:45", "الثانية عشرة إلا ربعاً"),
        ("9:05", "التاسعة وخمس دقائق"),
        ("9:02", "التاسعة ودقيقتان"),
        ("9:01", "التاسعة ودقيقة واحدة"),
        ("0:30", "الثانية عشرة والنصف"),
        ("13:30", "الواحدة والنصف"),
    ],
)
def test_speak_time(text: str, expected: str) -> None:
    assert nass.speak(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("50%", "خمسون بالمئة"),
        ("٥٠٪", "خمسون بالمئة"),
        ("3.5%", "ثلاثة فاصلة خمسة بالمئة"),
    ],
)
def test_speak_percent(text: str, expected: str) -> None:
    assert nass.speak(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("3.5", "ثلاثة فاصلة خمسة"),
        ("0.25", "صفر فاصلة اثنان خمسة"),
    ],
)
def test_speak_decimal(text: str, expected: str) -> None:
    assert nass.speak(text) == expected


def test_speak_date_levantine() -> None:
    assert nass.speak("3/4/2026") == "الثالث من نيسان عام ألف وستة وعشرون"


def test_speak_date_egyptian() -> None:
    assert nass.speak("3/4/2026", months="egyptian") == "الثالث من أبريل عام ألف وستة وعشرون"


def test_speak_rejects_unknown_months() -> None:
    with pytest.raises(ValueError):
        nass.speak("3/4/2026", months="klingon")


def test_speak_integer() -> None:
    assert nass.speak("2026") == "ألف وستة وعشرون"


def test_speak_leaves_words_alone() -> None:
    assert nass.speak("مرحبا بالعالم") == "مرحبا بالعالم"


def test_speak_mixed_sentence() -> None:
    out = nass.speak("وصلت الساعة 12:30 يوم 3/4/2026")
    assert "الثانية عشرة والنصف" in out
    assert "الثالث من نيسان" in out
    assert "12:30" not in out


def test_speak_empty() -> None:
    assert nass.speak("") == ""


def test_speak_invalid_time_does_not_crash() -> None:
    assert isinstance(nass.speak("99:99"), str)
