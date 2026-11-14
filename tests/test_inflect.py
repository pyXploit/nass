"""Tests for the sourced plural and dual lexicon."""

from __future__ import annotations

import pytest

from nass import dual, duals, glosses, known, plural, plurals


def test_plural_basic() -> None:
    assert plural("كتاب") == "كتب"
    assert plural("بيت") == "بيوت"
    assert plural("قلم") == "أقلام"


def test_plural_broken_and_sound() -> None:
    assert "مدارس" in plurals("مدرسة")
    assert "مدرسات" in plurals("مدرسة")
    assert "طالبون" in plurals("طالب")


def test_plural_irregular() -> None:
    assert plural("امرأة") == "نساء"
    assert plural("يوم") == "أيام"


def test_plural_loanword_is_sourced_not_generated() -> None:
    # The lexicon knows these; nothing is derived by rule.
    assert plural("كمبيوتر") == "كمبيوترات"
    assert plural("بنك") == "بنوك"


def test_dual() -> None:
    assert dual("كتاب") == "كتابان"
    assert dual("سيارة") == "سيارتان"
    assert dual("مدرسة") == "مدرستان"


def test_dual_variants() -> None:
    assert duals("ماء") == ["ماءان", "ماوان", "مايان"]


def test_vocalized() -> None:
    assert plural("كتاب", vocalized=True) == "كُتُب"
    assert dual("كتاب", vocalized=True) == "كِتَابَان"
    assert plural("مدرسة", vocalized=True) == "مَدْرَسَات"


def test_vocalized_drops_the_case_ending_before_a_shadda() -> None:
    # بَطٌّ ends in tanwin + shadda: the tanwin goes, the shadda stays.
    assert "بَطّ" in plurals("بطة", vocalized=True)
    assert "بَطٌّ" not in plurals("بطة", vocalized=True)


def test_researched_gap_fills() -> None:
    # These lemmas had no plural in the Wiktionary extract; the forms are quoted
    # from the Arabic dictionaries recorded in tools/gap_fills.json.
    assert plural("موزة") == "موز"
    assert plural("نحلة") == "نحل"
    assert plural("قش") == "قشوش"
    assert plural("أراك") == "أرك"
    assert plural("جبنة") == "أجبان"
    assert plural("بطة") == "بطط"


def test_no_rule_made_plurals() -> None:
    # No dictionary attests a plural for ماسة, so nothing is invented: it stays
    # unknown rather than get a sound feminine plural by rule.
    assert known("ماسة") is True
    assert plural("ماسة") is None


def test_second_source_fills_a_gap() -> None:
    # Wiktionary has no plural for زجاجة; arramooz does, so the gap is filled
    # from a dictionary rather than from the sound-plural rule.
    assert plural("زجاجة") == "زجاجات"


def test_collectives_are_known_but_have_no_plural() -> None:
    # موز and بصل are collectives: the word itself covers any number, so there
    # is no plural form to return, but the lemma is not unknown either.
    assert known("موز") is True
    assert plural("موز") is None
    assert known("بصل") is True
    assert plural("بصل") is None


def test_unknown_returns_none_not_a_guess() -> None:
    assert plural("زززز") is None
    assert dual("زززز") is None
    assert plurals("زززز") == []
    assert duals("زززز") == []
    assert known("زززز") is False


def test_lookup_ignores_diacritics() -> None:
    assert plural("كِتَاب") == "كتب"
    assert plural("كِتَابٌ") == "كتب"
    assert known("كِتَاب") is True


def test_lookup_strips_the_definite_article() -> None:
    assert plural("الكتاب") == "كتب"
    assert plural("السيارة") == "سيارات"
    assert dual("البيت") == "بيتان"
    assert known("الكتاب") is True


def test_article_exceptions_are_not_stripped() -> None:
    # These begin with ال but do not carry the article; stripping would
    # look up a different lexeme (الأولى -> أولى, اللهم -> لهم).
    assert plural("الأولى") is None
    assert plural("اللهم") is None
    assert plural("الآن") is None


def test_homographs_are_ranked_not_merged() -> None:
    # كتاب is both "book" and "Qur'an school"; the common sense comes first.
    assert plural("كتاب") == "كتب"
    assert plurals("كتاب") == ["كتب", "كتاتيب"]
    assert glosses("كتاب") == ["book", "a traditional school for teaching Qur'an"]


def test_glosses_absent_for_single_entry() -> None:
    assert glosses("زززز") == []


def test_known() -> None:
    assert known("كتاب") is True
    assert known("مدرسة") is True


@pytest.mark.parametrize("word", ["كتاب", "مدرسة", "سيارة", "بيت", "رجل", "ماء"])
def test_every_form_is_arabic(word: str) -> None:
    for form in plurals(word) + duals(word):
        assert form
        assert all("\u0600" <= ch <= "\u06ff" for ch in form)
