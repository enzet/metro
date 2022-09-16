import json
import logging
from pathlib import Path

from metro.core.map import Map
from metro.core.system import System
from metro.harvest.wikidata import WikidataCityParser, WikidataParser


if __name__ == "__main__":

    logging.basicConfig(format="%(levelname)s %(message)s", level=logging.INFO)

    map_: Map = Map()
    map_.local_languages = ["cz"]
    map_.systems = {"metro": System("metro")}

    cache_directory: Path = Path("cache")
    cache_directory.mkdir(exist_ok=True)

    wikidata_parser: WikidataParser = WikidataParser(cache_directory)

    parser = WikidataCityParser(wikidata_parser, map_, {190271: "metro"}, [1877386], 190271, [])
    parser.parse()

    for system in map_.get_systems():
        print(json.dumps(system.to_structure(), indent=4))
