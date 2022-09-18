from metro.core.system import Map, System
from metro.harvest.wikidata import WikidataCityParser


class MockWikidataParser:
    @staticmethod
    def parse_wikidata(wikidata_id: int) -> dict:
        if wikidata_id in [1, 2]:
            return {"entities": {f"Q{wikidata_id}": {"claims": {}}}}


def test_simple() -> None:
    wikidata_parser: MockWikidataParser = MockWikidataParser()
    map_: Map = Map("test_map")
    map_.local_languages = ["cz"]
    map_.systems = {"metro": System({}, "metro")}
    parser: WikidataCityParser = WikidataCityParser(wikidata_parser, map_, {1: "metro"}, [2], 1, [])
    parser.parse()
