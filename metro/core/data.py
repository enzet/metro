"""
This module is for text data manipulation: language-related parsing (if it more than just translation, for this - i18n,
dates, any kind of names, captions, etc.
"""
import logging
import re
from datetime import date
from typing import Any, Optional

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"


EN_SYSTEM_TYPE: str = "[Mm]etro|London [Uu]nderground|[Uu]nderground|[Tt]ube|[Ss]ubway|[Rr]ailway"
EN_CAPTION: str = f"(?P<name>((?!([Ss]tation|{EN_SYSTEM_TYPE})).)*)"

station_name_dict: dict[str, list[str]] = {
    "az": ["^(?P<name>.*) metrostansiyası"],
    "be": ["^Станцыя метро (?P<name>.*)$"],
    "be-tarask": ["^(?P<name>.*) \\(станцыя мэтро\\)$"],
    "bg": ["^Метростанция „(?P<name>.*)“$"],
    "bn": ["^(?P<name>.*) মেট্রো স্টেশন$"],
    "de": ["^Bahnhof (?P<name>.*)$", "^U-Bahnhof (?P<name>.*)$", "^S-Bahnhof (?P<name>.*)$"],
    "en": [
        f"^{EN_CAPTION}( \\(?({EN_SYSTEM_TYPE})( )?[Ss]tation(s)?\\)?)$",
        f"^{EN_CAPTION} \\((?P<line>.*)[ _][Ll]ine\\)$",
        f"^{EN_CAPTION}( [Ss]tation(s)?)?$",
        f"^{EN_CAPTION}(#.*({EN_SYSTEM_TYPE}))?( stations)?$",
        f"^{EN_CAPTION} ({EN_SYSTEM_TYPE})$",
        f"^{EN_CAPTION}( \\(.* ({EN_SYSTEM_TYPE})\\))?$",
        "^(?P<name>.* Railway Station) metro station$",
    ],
    "fi": ["^(?P<name>.*) metroasema$"],
    "it": ["^(?P<name>.*) \\(.*\\)$", "^(?P<name>.*)-(Kol'cevaja|Radial'naja)$"],
    "ja": ["^(?P<name>.*)駅( \\(.*\\))?$"],
    "nl": ["^(?P<name>.*) \\(metrostation\\)$"],
    "pl": ["^Stacja (?P<name>.*)$"],
    "pt": ["^Estação (?P<name>.*)$"],
    "ru": [
        "^(?P<name>.*) \\(станция метро\\)$",
        "^(?P<name>.*) \\(станция метро, .* линия\\)$",
        "^(?P<name>.*) \\(станция метро, .*\\)$",
    ],
    "tt": ["^(?P<name>.*) \\(метро станциясе\\)$"],
    "uk": ["^(?P<name>.*) \\(станція метро\\)$", "^(?P<name>.*) \\(станція метро, (?P<city>.*)\\)$"],
    "zh": [
        "^(?P<name>.*)站$",
    ],
}


def extract_station_name(name: str, language: str) -> str:
    """
    Station name extraction from it"s caption (which is used for Wikipedia or Wikidata page names). For example, for
    "Baker Street station (London Underground)" it should give "Baker Street".

    :param: name: input station name
    """
    name = name.replace("&", "and")

    if language in station_name_dict:
        for pattern in station_name_dict[language]:
            if m := re.match(pattern, name):
                return m.group("name")
    return name


def compute_short_station_id(names: dict[str, str], local_languages: list[str]) -> Optional[str]:
    """
    Create station short identifier.

    :param names: names in different languages.
    :param local_languages: primary languages for the region.
    :return: station ID or None.
    """
    if not names:
        logging.error("cannot compute station ID, no names")
        return None
    for language in ["en"] + local_languages + list(sorted(names.keys())):
        if language in names:
            return extract_station_name(names[language], language)


line_name_dict = {
    "be": [
        "^(?P<name>.*) лінія$",
    ],
    "en": [
        "^(?P<name>.*) \\(.*\\)$",
        "^(?P<name>.*) [Ll]ine$",
        "^[Ll]ine (?P<name>.*)$",
        "^.* [Mm]etro [Ll]ine (?P<name>.*)$",
        "^(?P<name>.*) [Rr]ailway$",
    ],
    "ru": [
        "^(?P<name>.*) линия$",
    ],
    "uk": [
        "^(?P<name>.*) лінія$",
    ],
}


def extract_line_name(name: str, language: str):
    """
    Try to remove all specifiers from the line caption.

    :param name: line caption with probably some specifiers.
    :param language: language of the name.
    :return: pure line caption.
    """
    if language in line_name_dict:
        for pattern in line_name_dict[language]:
            if matcher := re.match(pattern, name):
                return matcher.group("name")

    return name


def compute_line_id(names: dict[str, Any], local_languages: list[str] = None) -> Optional[str]:
    """
    Compute line identifier using its names in different languages.

    :param names: names of the line.
    :param local_languages: local language identifiers of the area this line belongs to.
    """
    if not names:
        logging.error("cannot compute line ID, no names")
        return None

    output: str = ""

    if local_languages is None:
        local_languages = []

    # Sort language identifiers to make the result more predictable.
    for language in ["en"] + local_languages + list(sorted(names.keys())):
        if language in names:
            return extract_line_name(names[language], language)

    return output


def get_date(string_date):
    """
    Parsing date from [[DD.]MM.]YYYY representation.

    :param: string_date: date [[DD.]MM.]YYYY representation
    :return: date and accuracy (may be "year", "month", or "day")
    """
    year, month, day = 1, 1, 1
    accuracy = "none"

    if m := re.match("^(?P<year>\\d\\d\\d\\d)$", string_date):
        year = int(m.group("year"))
        accuracy = "year"

    if m := re.match("^(?P<month>\\d\\d)[.\\- ](?P<year>\\d\\d\\d\\d)$", string_date):
        month = int(m.group("month"))
        year = int(m.group("year"))
        accuracy = "month"

    if m := re.match("^(?P<day>\\d\\d)[.\\- ](?P<month>\\d\\d)[.\\- ](?P<year>\\d\\d\\d\\d)$", string_date):
        day = int(m.group("day"))
        month = int(m.group("month"))
        year = int(m.group("year"))
        accuracy = "day"

    return date(year, month, day), accuracy


def get_date_representation(string_date, language, translator):
    """Date representation parsing from [[DD.]MM.]YYYY representation."""
    d, accuracy = get_date(string_date)
    if accuracy == "year":
        return d.strftime("%Y")
    if accuracy == "month":
        if language == "en":
            return d.strftime("%B %Y")
        else:
            return translator[d.strftime("%B").lower()][language + "-rod"] + d.strftime(" %Y")
    if accuracy == "day":
        if language == "en":
            return str(d.day) + d.strftime(" %B %Y")
        else:
            return str(d.day) + translator[d.strftime("%B").lower()][language + "-rod"] + d.strftime(" %Y")
