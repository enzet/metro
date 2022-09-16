"""
This module is for text data manipulation: language-related parsing (if it more than just translation, for this - i18n,
dates, any kind of names, captions, etc.
"""
import logging
import re
from datetime import date
from typing import Any, Dict, List, Optional

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"

en_system_type = "[Mm]etro|London [Uu]nderground|[Uu]nderground|[Tt]ube|[Ss]ubway|[Rr]ailway"
en_caption = "(?P<name>((?!([Ss]tation|" + en_system_type + ")).)*)"

station_name_dict = {
    "az": ["^(?P<name>.*) metrostansiyası"],
    "be": ["^Станцыя метро (?P<name>.*)$"],
    "be-tarask": ["^(?P<name>.*) \\(станцыя мэтро\\)$"],
    "bg": ["^Метростанция „(?P<name>.*)“$"],
    "bn": ["^(?P<name>.*) মেট্রো স্টেশন$"],
    "de": ["^Bahnhof (?P<name>.*)$", "^U-Bahnhof (?P<name>.*)$", "^S-Bahnhof (?P<name>.*)$"],
    "en": [
        "^" + en_caption + "( \\(?(" + en_system_type + ")( )?[Ss]tation(s)?\\)?)$",
        "^" + en_caption + " \\((?P<line>.*)[ _][Ll]ine\\)$",
        "^" + en_caption + "( [Ss]tation(s)?)?$",
        "^" + en_caption + "(#.*(" + en_system_type + "))?( stations)?$",
        "^" + en_caption + " (" + en_system_type + ")$",
        "^" + en_caption + "( \\(.* (" + en_system_type + ")\\))?$",
        "^(?P<name>.* Railway Station) metro station$",
    ],  # very special case
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

    if language == "en" and name == "Nangloi Railway station":
        return name

    if language in station_name_dict:
        for pattern in station_name_dict[language]:
            m = re.match(pattern, name)
            if m:
                return m.group("name")
    return name


def compute_short_station_id(names: Dict[str, str], local_languages: List[str]) -> Optional[str]:
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
            return escape(extract_station_name(names[language], language))


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
    :return: pure line caption.
    """
    replacements = {
        # "Moscow Central Ring": "Moscow Central Circle",
    }

    if language in line_name_dict:
        for pattern in line_name_dict[language]:
            m = re.match(pattern, name)
            if m:
                return m.group("name")

    if name in replacements:
        name = replacements[name]

    return name


def compute_line_id(names: Dict[str, Any], local_languages: List[str] = None) -> Optional[str]:
    """
    Compute line identifier using its names in different languages.

    :param names: names of the line.
    :param local_languages: local language identifiers of the area this line belongs to.
    """
    if not names:
        logging.error("cannot compute line ID, no names")
        return None

    output = ""

    if local_languages is None:
        local_languages = []

    # We sort language identifiers to make the result more predictable.
    for language in ["en"] + local_languages + list(sorted(names.keys())):
        if language in names:
            return escape(extract_line_name(names[language], language))

    return output


def river_name(name, language):
    """
    River name extraction from it"s caption (which is used for Wikipedia or Wikidata page names). For example, for
    "Dnieper River" it should give "Dnieper".

    :param: name: input river name
    :return: cropped river name
    """
    if language == "en":
        m = re.match("^(?P<name>.*) River$", name)
        if m:
            return m.group("name")
    return name


def get_date(string_date):
    """
    Parsing date from [[DD.]MM.]YYYY representation.

    :param: string_date: date [[DD.]MM.]YYYY representation
    :return: date and accuracy (may be "year", "month", or "day")
    """
    year, month, day = 1, 1, 1
    accuracy = "none"

    m = re.match("^(?P<year>\\d\\d\\d\\d)$", string_date)
    if m:
        year = int(m.group("year"))
        accuracy = "year"

    m = re.match("^(?P<month>\\d\\d)[.\\- ](?P<year>\\d\\d\\d\\d)$", string_date)
    if m:
        month = int(m.group("month"))
        year = int(m.group("year"))
        accuracy = "month"

    m = re.match("^(?P<day>\\d\\d)[.\\- ](?P<month>\\d\\d)[.\\- ](?P<year>\\d\\d\\d\\d)$", string_date)
    if m:
        day = int(m.group("day"))
        month = int(m.group("month"))
        year = int(m.group("year"))
        accuracy = "day"

    return date(year, month, day), accuracy


def get_date_representation(string_date, language, translator):
    """
    Date representation parsing from [[DD.]MM.]YYYY representation.
    """
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


ru_to_en = [
    [
        "а",
        "б",
        "в",
        "г",
        "д",
        "е",
        "ё",
        "ж",
        "з",
        "и",
        "й",
        "к",
        "л",
        "м",
        "н",
        "о",
        "п",
        "р",
        "с",
        "т",
        "у",
        "ф",
        "х",
        "ц",
        "ч",
        "ш",
        "щ",
        "ъ",
        "ы",
        "ь",
        "э",
        "ю",
        "я",
    ],
    [
        "a",
        "b",
        "v",
        "g",
        "d",
        "ye",
        "yo",
        "zh",
        "z",
        "i",
        "y",
        "k",
        "l",
        "m",
        "n",
        "o",
        "p",
        "r",
        "s",
        "t",
        "u",
        "f",
        "kh",
        "ts",
        "ch",
        "sh",
        "sch",
        "",
        "y",
        "",
        "e",
        "yu",
        "ya",
    ],
]


def escape(text):
    text = text.lower()
    escaped = ""
    special = False
    for c in text:
        if c in " :-+=\\/-–—()'\"«»ʻ,.*!@#$%^º’":
            if not special:
                escaped += "_"
            special = True
            continue
        else:
            special = False
        if c in ru_to_en[0]:
            escaped += ru_to_en[1][ru_to_en[0].index(c)]
        elif c in "№":
            escaped += "n"
        elif c in "&":
            escaped += "and"
        elif c in "àáâäãåā":
            escaped += "a"
        elif c in "æ":
            escaped += "ae"
        elif c in "çćčə":
            escaped += "c"
        elif c in "èéêëēėęě":
            escaped += "e"
        elif c in "ğ":
            escaped += "g"
        elif c in "ĥ":
            escaped += "h"
        elif c in "îïíīįìıii̇і":
            escaped += "i"
        elif c in "ĵ":
            escaped += "j"
        elif c in "ł":
            escaped += "l"
        elif c in "ñńň":
            escaped += "n"
        elif c in "õōøôöòó":
            escaped += "o"
        elif c in "œ":
            escaped += "oe"
        elif c in "ß":
            escaped += "ss"
        elif c in "ř":
            escaped += "r"
        elif c in "śšş":
            escaped += "s"
        elif c in "ûüùúūůŭ":
            escaped += "u"
        elif c in "ÿýў":
            escaped += "y"
        elif c in "žźż":
            escaped += "z"
        else:
            escaped += c

    while escaped[0] == "_":
        escaped = escaped[1:]
    while escaped[-1] == "_":
        escaped = escaped[:-1]
    while "__" in escaped:
        escaped = escaped.replace("__", "_")

    for c in escaped:
        if not ("a" <= c <= "z" or "0" <= c <= "9" or c == "_"):
            logging.warning("not ASCII: " + escaped + ", symbol <" + c + ">")

    return escaped