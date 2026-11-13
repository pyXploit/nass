"""Normalisation for speech synthesis.

Screen readers and TTS engines read Arabic digits, times and dates badly: they
spell out the glyphs, or read "12:30" as "twelve colon thirty". :func:`speak`
rewrites those into the words a person would actually say.
"""

from __future__ import annotations

import re

from nass.numbers import to_western_digits, words

__all__ = ["speak"]

_HOURS = (
    "",
    "الواحدة",
    "الثانية",
    "الثالثة",
    "الرابعة",
    "الخامسة",
    "السادسة",
    "السابعة",
    "الثامنة",
    "التاسعة",
    "العاشرة",
    "الحادية عشرة",
    "الثانية عشرة",
)

# Masculine numeral forms, used with feminine counted nouns (3-10).
_MASCULINE_UNITS = (
    "",
    "واحد",
    "اثنان",
    "ثلاث",
    "أربع",
    "خمس",
    "ست",
    "سبع",
    "ثمان",
    "تسع",
    "عشر",
)

_MONTHS = {
    "levantine": (
        "كانون الثاني",
        "شباط",
        "آذار",
        "نيسان",
        "أيار",
        "حزيران",
        "تموز",
        "آب",
        "أيلول",
        "تشرين الأول",
        "تشرين الثاني",
        "كانون الأول",
    ),
    "egyptian": (
        "يناير",
        "فبراير",
        "مارس",
        "أبريل",
        "مايو",
        "يونيو",
        "يوليو",
        "أغسطس",
        "سبتمبر",
        "أكتوبر",
        "نوفمبر",
        "ديسمبر",
    ),
}

_TIME = re.compile(r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)(?!\d)")
_DATE = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{4})(?!\d)")
_PERCENT = re.compile(r"(?<!\d)(\d+(?:\.\d+)?)\s*[%٪]")
_DECIMAL = re.compile(r"(?<!\d)(\d+)\.(\d+)(?!\d)")
_INTEGER = re.compile(r"\d+")

_ORDINAL_DAYS = (
    "",
    "الأول",
    "الثاني",
    "الثالث",
    "الرابع",
    "الخامس",
    "السادس",
    "السابع",
    "الثامن",
    "التاسع",
    "العاشر",
    "الحادي عشر",
    "الثاني عشر",
    "الثالث عشر",
    "الرابع عشر",
    "الخامس عشر",
    "السادس عشر",
    "السابع عشر",
    "الثامن عشر",
    "التاسع عشر",
    "العشرون",
    "الحادي والعشرون",
    "الثاني والعشرون",
    "الثالث والعشرون",
    "الرابع والعشرون",
    "الخامس والعشرون",
    "السادس والعشرون",
    "السابع والعشرون",
    "الثامن والعشرون",
    "التاسع والعشرون",
    "الثلاثون",
    "الحادي والثلاثون",
)


def _minutes(n: int) -> str:
    # دقيقة is feminine, so 3-10 take the masculine numeral form: خمس دقائق,
    # not خمسة دقائق.
    if n == 1:
        return "دقيقة واحدة"
    if n == 2:
        return "دقيقتان"
    if 3 <= n <= 10:
        return f"{_MASCULINE_UNITS[n]} دقائق"
    return f"{words(n)} دقيقة"


def _time(hour: int, minute: int) -> str:
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return f"{hour}:{minute:02d}"
    spoken = _HOURS[hour % 12 or 12]
    if minute == 0:
        return f"{spoken} تماماً"
    if minute == 15:
        return f"{spoken} والربع"
    if minute == 30:
        return f"{spoken} والنصف"
    # Past the half hour Arabic counts down to the next hour: 9:45 is
    # العاشرة إلا ربعاً, not التاسعة إلا ربعاً.
    if minute > 30:
        following = _HOURS[(hour + 1) % 12 or 12]
        if minute == 45:
            return f"{following} إلا ربعاً"
        return f"{following} إلا {_minutes(60 - minute)}"
    return f"{spoken} و{_minutes(minute)}"


def _decimal(whole: str, fraction: str) -> str:
    digits = " ".join(words(int(d)) for d in fraction)
    return f"{words(int(whole))} فاصلة {digits}"


def speak(text: str, *, months: str = "levantine") -> str:
    """Rewrite numbers, times, dates and percentages as spoken Arabic.

    >>> speak("الساعة 12:30")
    'الساعة الثانية عشرة والنصف'
    >>> speak("50%")
    'خمسون بالمئة'
    """
    if months not in _MONTHS:
        raise ValueError(f"months must be one of {sorted(_MONTHS)}")
    month_names = _MONTHS[months]

    out = to_western_digits(text)

    def time_sub(match: re.Match[str]) -> str:
        return _time(int(match.group(1)), int(match.group(2)))

    def date_sub(match: re.Match[str]) -> str:
        day, month, year = (int(g) for g in match.groups())
        if not 1 <= day <= 31 or not 1 <= month <= 12:
            return match.group(0)
        return f"{_ORDINAL_DAYS[day]} من {month_names[month - 1]} عام {words(year)}"

    def percent_sub(match: re.Match[str]) -> str:
        value = match.group(1)
        if "." in value:
            whole, fraction = value.split(".", 1)
            return f"{_decimal(whole, fraction)} بالمئة"
        return f"{words(int(value))} بالمئة"

    def decimal_sub(match: re.Match[str]) -> str:
        return _decimal(match.group(1), match.group(2))

    out = _TIME.sub(time_sub, out)
    out = _DATE.sub(date_sub, out)
    out = _PERCENT.sub(percent_sub, out)
    out = _DECIMAL.sub(decimal_sub, out)
    out = _INTEGER.sub(lambda m: words(int(m.group(0))), out)
    return out
