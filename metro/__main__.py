import json
import logging
from pathlib import Path

from metro.core.system import System, Map
from metro.harvest.wikidata import WikidataCityParser, WikidataParser

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"


if __name__ == "__main__":

    logging.basicConfig(format="%(levelname)s %(message)s", level=logging.INFO)

    map_: Map = Map("prague_metro")
    map_.local_languages = ["cz"]
    map_.systems = {"metro": System({}, "metro")}

    cache_directory: Path = Path("cache")
    cache_directory.mkdir(exist_ok=True)

    wikidata_parser: WikidataParser = WikidataParser(cache_directory)

    parser = WikidataCityParser(wikidata_parser, map_, {190271: "metro"}, [1877386], 190271, [])
    parser.parse()

    output_directory: Path = Path("out") / map_.id_
    output_directory.mkdir(parents=True, exist_ok=True)

    for system in map_.systems.values():
        with (output_directory / f"{system.id_}.json").open("w+") as output_file:
            json.dump(system.serialize(), output_file, indent=4, ensure_ascii=False)
        with (output_directory / f"{system.id_}.json").open() as input_file:
            System({}, system.id_).deserialize(json.load(input_file))
