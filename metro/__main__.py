import argparse
import json
import logging
import sys
from pathlib import Path

from metro.core.system import System, Map
from metro.harvest.wikidata import WikidataCityParser, WikidataParser

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"


def main():
    logging.basicConfig(format="%(levelname)s %(message)s", level=logging.INFO)

    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("--system-wikidata-id")
    parser.add_argument("--station-wikidata-ids", nargs="+")
    parser.add_argument("--cache", default="cache")
    arguments = parser.parse_args(sys.argv[1:])

    cache_directory: Path = Path(arguments.cache)
    cache_directory.mkdir(exist_ok=True)

    wikidata_parser: WikidataParser = WikidataParser(cache_directory)
    map_: Map = Map("metro", {}, {"metro": System({}, "metro")}, ["en"])

    city_parser: WikidataCityParser = WikidataCityParser(
        wikidata_parser,
        map_,
        {int(arguments.system_wikidata_id): "metro"},
        [int(x) for x in arguments.station_wikidata_ids],
        int(arguments.system_wikidata_id),
        [],
    )
    city_parser.parse()

    output_directory: Path = Path("out")
    output_directory.mkdir(parents=True, exist_ok=True)

    system: System = map_.systems["metro"]
    with (output_directory / f"{system.id_}.json").open("w+") as output_file:
        json.dump(system.serialize(), output_file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
