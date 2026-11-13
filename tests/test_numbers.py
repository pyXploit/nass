"""Tests for nass.numbers."""

from __future__ import annotations

import pytest

import nass


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (0, "صفر"),
        (1, "واحد"),
        (2, "اثنان"),
        (3, "ثلاثة"),
        (9, "تسعة"),
        (10, "عشرة"),
        (11, "أحد عشر"),
        (12, "اثنا عشر"),
        (19, "تسعة عشر"),
        (20, "عشرون"),
        (21, "واحد وعشرون"),
        (34, "أربعة وثلاثون"),
        (99, "تسعة وتسعون"),
        (100, "مئة"),
        (101, "مئة وواحد"),
        (110, "مئة وعشرة"),
        (200, "مئتان"),
        (300, "ثلاثمئة"),
        (999, "تسعمئة وتسعة وتسعون"),
        (1000, "ألف"),
        (2000, "ألفان"),
        (2001, "ألفان وواحد"),
        (2003, "ألفان وثلاثة"),
        (2026, "ألفان وستة وعشرون"),
        (2100, "ألفان ومئة"),
        (3000, "ثلاثة آلاف"),
        (10000, "عشرة آلاف"),
        (11000, "أحد عشر ألفاً"),
        (100000, "مئة ألف"),
        (200000, "مئتا ألف"),
        (1000000, "مليون"),
        (2000000, "مليونان"),
        (3000000, "ثلاثة ملايين"),
        (1000000000, "مليار"),
        (1234, "ألف ومئتان وأربعة وثلاثون"),
    ],
)
def test_words(n: int, expected: str) -> None:
    assert nass.words(n) == expected


def test_words_negative() -> None:
    assert nass.words(-5) == "سالب خمسة"


def test_words_out_of_range() -> None:
    with pytest.raises(ValueError):
        nass.words(1_000_000_000_000)


@pytest.mark.parametrize(
    ("n", "kwargs", "expected"),
    [
        (1, {}, "١ كتاب"),
        (2, {"dual": "كتابان"}, "٢ كتابان"),
        (3, {"plural": "كتب"}, "٣ كتب"),
        (10, {"plural": "كتب"}, "١٠ كتب"),
        (11, {"accusative": "كتابًا"}, "١١ كتابًا"),
        (99, {"accusative": "كتابًا"}, "٩٩ كتابًا"),
        (100, {}, "١٠٠ كتاب"),
        (103, {"plural": "كتب"}, "١٠٣ كتب"),
        (111, {"accusative": "كتابًا"}, "١١١ كتابًا"),
    ],
)
def test_count(n: int, kwargs: dict[str, str], expected: str) -> None:
    assert nass.count(n, "كتاب", **kwargs) == expected


def test_count_western_digits() -> None:
    assert nass.count(3, "كتاب", plural="كتب", arabic_digits=False) == "3 كتب"


def test_count_rejects_negative() -> None:
    with pytest.raises(ValueError):
        nass.count(-1, "كتاب")


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (1, "الأول"),
        (2, "الثاني"),
        (3, "الثالث"),
        (10, "العاشر"),
        (11, "الحادي عشر"),
        (12, "الثاني عشر"),
        (20, "العشرون"),
        (21, "الحادي والعشرون"),
        (22, "الثاني والعشرون"),
        (30, "الثلاثون"),
        (99, "التاسع والتسعون"),
    ],
)
def test_ordinal(n: int, expected: str) -> None:
    assert nass.ordinal(n) == expected


@pytest.mark.parametrize("n", [0, 100])
def test_ordinal_out_of_range(n: int) -> None:
    with pytest.raises(ValueError):
        nass.ordinal(n)


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (0, "zero"),
        (1, "one"),
        (2, "two"),
        (3, "few"),
        (10, "few"),
        (11, "many"),
        (99, "many"),
        (100, "other"),
        (103, "few"),
        (111, "many"),
        (1000, "other"),
    ],
)
def test_plural_category(n: int, expected: str) -> None:
    assert nass.plural_category(n) == expected


def test_digits_round_trip() -> None:
    assert nass.to_arabic_digits("2026") == "٢٠٢٦"
    assert nass.to_western_digits("٢٠٢٦") == "2026"
    assert nass.to_western_digits("۲۰۲۶") == "2026"
    assert nass.to_western_digits(nass.to_arabic_digits("1234567890")) == "1234567890"
