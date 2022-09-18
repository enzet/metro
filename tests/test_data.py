"""
Map Machine.

Author: Sergey Vartanov (me@enzet.ru)
"""
from metro.core.data import extract_line_name, extract_station_name


stations = {
    "az": [
        ["Qara Qarayev metrostansiyası", "Qara Qarayev"],
    ],
    "be": [
        ["Станцыя метро Уручча", "Уручча"],
    ],
    "be-tarask": [
        ["Акадэммястэчка (станцыя мэтро)", "Акадэммястэчка"],
    ],
    "bg": [
        ["Метростанция „Обеля“", "Обеля"],
    ],
    "bn": [
        ["নোয়াপাড়া মেট্রো স্টেশন", "নোয়াপাড়া"],
    ],
    "en": [
        ["Uralskaya (Yekaterinburg Metro)", "Uralskaya"],
        ["Baker Street tube station", "Baker Street"],
        ["Barakhamba Road metro station", "Barakhamba Road"],
        ["Aldwych Underground", "Aldwych"],
        ["Hampstead London Underground station", "Hampstead"],
        ["Kiyevskaya (Koltsevaya Line)", "Kiyevskaya"],
        ["Maidan Nezalezhnosti (metrostation)", "Maidan Nezalezhnosti"],
        ["Fudōin-mae Station", "Fudōin-mae"],
        ["Railway Station", "Railway Station"],
    ],
    "fi": [
        ["Almalyn metroasema", "Almalyn"],
    ],
    "it": [
        ["Kievskaja-Kol'cevaja", "Kievskaja"],
        ["Kievskaja (Filëvskaja)", "Kievskaja"],
        ["Kurskaja-Radial'naja", "Kurskaja"],
        ["Žytomyrs'ka (metropolitana di Kiev)", "Žytomyrs'ka"],
    ],
    "nl": [
        ["Zjytomyrska (metrostation)", "Zjytomyrska"],
    ],
    "ja": [
        ["長楽寺駅", "長楽寺"],
        ["大町駅 (広島県)", "大町"],
    ],
    "pl": [
        ["Stacja Zajelcowskaja", "Zajelcowskaja"],
    ],
    "pt": [
        ["Estação Zaieltsovskaia", "Zaieltsovskaia"],
    ],
    "ru": [
        ["Теремки (станция метро)", "Теремки"],
        ["Авиамоторная (станция метро, Калининско-Солнцевская линия)", "Авиамоторная"],
        ["Дустлик (станция метро, Ташкент)", "Дустлик"],
    ],
    "tt": [
        ["Авиатөзелеш (метро станциясе)", "Авиатөзелеш"],
    ],
    "uk": [
        ["Авіабудівельна (станція метро)", "Авіабудівельна"],
        ["Московська (станція метро, Казань)", "Московська"],
        ["Герцена (станція метро)", "Герцена"],
    ],
    "zh": [
        ["昆采沃站", "昆采沃"],
    ],
}

lines = {
    "be": [
        ["Аўтазаводская лінія", "Аўтазаводская"],
    ],
    "uk": [
        ["Святошинсько-Броварська лінія", "Святошинсько-Броварська"],
    ],
}


def test_data_stations():
    for language in sorted(stations.keys()):
        for test in stations[language]:
            parsed = extract_station_name(test[0], language)
            assert parsed == test[1]


def test_data_lines():
    for language in sorted(lines.keys()):
        for test in lines[language]:
            parsed = extract_line_name(test[0], language)
            assert parsed == test[1]
