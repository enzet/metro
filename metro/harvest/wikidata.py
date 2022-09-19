import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from metro.core import data, network
from metro.core.line import Line
from metro.core.station import ConnectionType, ObjectStatus, Station
from metro.core.system import Map, System

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"


WIKIDATA_ITEM_PREFIX = "Q"

WIKIDATA_PROPERTY_ROUTE_MAP = "P15"
WIKIDATA_PROPERTY_TRANSPORT_NETWORK = "P16"
WIKIDATA_PROPERTY_COUNTRY = "P17"
WIKIDATA_PROPERTY_INSTANCE_OF = "P31"
WIKIDATA_PROPERTY_LINE = "P81"
WIKIDATA_PROPERTY_ARCHITECT = "P84"
WIKIDATA_PROPERTY_LOCATED = "P131"
WIKIDATA_PROPERTY_LOGO_IMAGE = "P154"
WIKIDATA_PROPERTY_NEXT_STATION = "P197"
WIKIDATA_PROPERTY_STATION_CODE = "P296"
WIKIDATA_PROPERTY_PART_OF = "P361"
WIKIDATA_PROPERTY_COMPLEX_COLOR = "P462"
WIKIDATA_PROPERTY_COLOR = "P465"
WIKIDATA_PROPERTY_HAS_PART = "P527"
WIKIDATA_PROPERTY_TERMINUS = "P559"
WIKIDATA_PROPERTY_INCEPTION = "P571"
WIKIDATA_PROPERTY_CLOSE_DATE = "P576"
WIKIDATA_PROPERTY_END_DATE = "P582"
WIKIDATA_PROPERTY_COORDINATES = "P625"
WIKIDATA_PROPERTY_TRANSITION_STATION = "P833"
WIKIDATA_PROPERTY_NUMBER_OF_TRACKS = "P1103"
WIKIDATA_PROPERTY_DATE_OF_OFFICIAL_OPENING = "P1619"
WIKIDATA_PROPERTY_NATIVE_LABEL = "P1705"
WIKIDATA_PROPERTY_LENGTH = "P2043"
WIKIDATA_PROPERTY_VERTICAL_DEPTH = "P4511"

WIKIDATA_ITEM_YELLOW = "Q943"
WIKIDATA_ITEM_BLUE = "Q1088"
WIKIDATA_ITEM_GREEN = "Q3133"
WIKIDATA_ITEM_RED = "Q3142"
WIKIDATA_ITEM_BLACK = "Q23445"
WIKIDATA_ITEM_PINK = "Q429220"
WIKIDATA_ITEM_BROWN = "Q47071"
WIKIDATA_ITEM_WHITE = "Q23444"
WIKIDATA_ITEM_LIGHT_BLUE = "Q1602687"
WIKIDATA_ITEM_ORANGE = "Q39338"

WIKIDATA_ITEM_RAPID_TRANSIT = "Q5503"
WIKIDATA_ITEM_METER = "Q11573"
WIKIDATA_ITEM_RAILWAY_STATION = "Q55488"
WIKIDATA_ITEM_UNDERGROUND_RAILWAY_STATION = "Q55491"
WIKIDATA_ITEM_METRO_STATION = "Q928830"
WIKIDATA_ITEM_RAPID_TRANSIT_LINE = "Q15079663"
WIKIDATA_ITEM_STATION_LOCATED_UNDERGROUND = "Q22808403"
WIKIDATA_ITEM_STATION_LOCATED_ON_SURFACE = "Q22808404"

WIKIDATA_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class WikidataItem:
    """Item of Wikidata project."""

    def __init__(self, structure: dict, wikidata_id: int) -> None:
        """
        :param structure: Wikidata item structure
        :param wikidata_id: Wikidata item unique identifier
        """
        self.wikidata_id = wikidata_id

        if "entities" not in structure:
            logging.warning("no entities in Wikidata entity")
            self.entity = None
        if WIKIDATA_ITEM_PREFIX + str(wikidata_id) not in structure["entities"]:
            logging.error("bad Wikidata structure: no entity")
            self.entity = None
        self.entity = structure["entities"][WIKIDATA_ITEM_PREFIX + str(wikidata_id)]

        self.claims = self.entity["claims"] if "claims" in self.entity else {}

        self.names: dict[str, str] = {}
        if "labels" in self.entity:
            for language in self.entity["labels"]:
                self.names[language] = self.entity["labels"][language]["value"]

        self.descriptions: dict[str, str] = {}
        if "descriptions" in self.entity:
            for language in self.entity["descriptions"]:
                self.descriptions[language] = self.entity["descriptions"][language]["value"]

        self.aliases: dict[str, list[str]] = {}
        if "aliases" in self.entity:
            for language in self.entity["aliases"]:
                self.aliases[language] = []
                for alias in self.entity["aliases"][language]:
                    self.aliases[language].append(alias["value"])

        self.site_links: dict[str, str] = {}
        if "sitelinks" in self.entity:
            for site in self.entity["sitelinks"]:
                self.site_links[site] = self.entity["sitelinks"][site]["title"]

    def get_name(self, language: str = "en") -> Optional[str]:
        """
        Get item name in specified language if it exists.

        :param language: requested language of the name.
        """
        if "labels" not in self.entity or language not in self.entity["labels"]:
            return None
        return self.entity["labels"][language]["value"]

    def has_name(self, language: str = "en") -> bool:
        if "labels" not in self.entity:
            return False
        if language not in self.entity["labels"]:
            return False
        return (
            language in self.entity["labels"]
            and "value" in self.entity["labels"][language]
            and self.entity["labels"][language]["value"]
        )

    def get_any_name(self) -> str:
        """Get any item name if it exists."""
        if "labels" not in self.entity:
            return "unknown"
        if "en" in self.entity["labels"]:
            return self.entity["labels"]["en"]["value"]
        return next(iter(self.entity["labels"].values()))["value"]


class WikidataTime:
    def __init__(self, time_point: dict[str, Any]) -> None:
        time = time_point["time"]
        if time[6:8] == "00":
            time = time[:6] + "01" + time[8:]
        if time[9:11] == "00":
            time = time[:9] + "01" + time[11:]
        self.time = datetime.strptime(time, "+" + WIKIDATA_TIME_FORMAT)

        self.timezone = time_point["timezone"]
        self.precision = time_point["precision"]
        self.before = time_point["before"]
        self.after = time_point["after"]


def get_value(claim: dict):
    return claim["mainsnak"]["datavalue"]["value"]


class WikidataStationItem(WikidataItem):
    """
    Wikidata item that describes transport station. Note, that the station represented by the Wikidata item may differ
    from the station definition of the project.
    """

    type_map: dict[str, dict[str, ObjectStatus]] = {
        "en": {
            "prospective": ObjectStatus.PLANNED,
            "planned": ObjectStatus.PLANNED,
            "under construction": ObjectStatus.UNDER_CONSTRUCTION,
        },
        "ru": {
            "временно закрытая": ObjectStatus.CLOSED,
            "законсервированная": ObjectStatus.CLOSED,
            "перспективная": ObjectStatus.PLANNED,
            "проектируемая": ObjectStatus.PLANNED,
            "будущая": ObjectStatus.PLANNED,
            "строящаяся": ObjectStatus.UNDER_CONSTRUCTION,
        },
    }

    def __init__(self, structure: dict, wikidata_id: int) -> None:
        super().__init__(structure, wikidata_id)

        name: str = WIKIDATA_ITEM_PREFIX + str(wikidata_id)

        self.structure_type: Optional[str] = None

        if WIKIDATA_PROPERTY_INSTANCE_OF in self.claims:
            for claim in self.claims[WIKIDATA_PROPERTY_INSTANCE_OF]:
                if get_value(claim)["id"] == WIKIDATA_ITEM_METRO_STATION:
                    _ = "metro"
                if get_value(claim)["id"] == WIKIDATA_ITEM_STATION_LOCATED_ON_SURFACE:
                    self.structure_type = "ground"
                if get_value(claim)["id"] == WIKIDATA_ITEM_STATION_LOCATED_UNDERGROUND:
                    self.structure_type = "underground"

        self.system_wikidata_ids: set[int] = set()

        if WIKIDATA_PROPERTY_PART_OF in self.claims:
            self.system_wikidata_ids.add(get_value(self.claims[WIKIDATA_PROPERTY_PART_OF][0])["numeric-id"])

        if WIKIDATA_PROPERTY_TRANSPORT_NETWORK in self.claims:
            self.system_wikidata_ids.add(get_value(self.claims[WIKIDATA_PROPERTY_TRANSPORT_NETWORK][0])["numeric-id"])

        self.status = {}

        for language in self.type_map:
            if language in self.descriptions:
                for pattern in self.type_map[language]:
                    if pattern in self.descriptions[language].lower():
                        self.status = {"type": self.type_map[language][pattern]}
                        break

        self.open_time = None

        if WIKIDATA_PROPERTY_DATE_OF_OFFICIAL_OPENING in self.claims:
            if "datavalue" not in self.claims[WIKIDATA_PROPERTY_DATE_OF_OFFICIAL_OPENING][0]["mainsnak"]:
                logging.warning("[WIKIDATA] no value for date of official opening for " + name)
            else:
                point = get_value(self.claims[WIKIDATA_PROPERTY_DATE_OF_OFFICIAL_OPENING][0])
                try:
                    wikidata_time = WikidataTime(point)
                    self.open_time = wikidata_time.time
                    if wikidata_time.time > datetime.now():
                        self.status = {"type": ObjectStatus.UNDER_CONSTRUCTION}
                except ValueError:
                    logging.warning("Invalid date: " + str(point))

        self.geo_position: Optional[tuple[float, float]] = None
        self.altitude: Optional[float] = None

        if WIKIDATA_PROPERTY_COORDINATES in self.claims:
            geo_structure: dict[str, float] = get_value(self.claims[WIKIDATA_PROPERTY_COORDINATES][0])
            self.geo_position = (geo_structure["latitude"], geo_structure["longitude"])
            if "altitude" in geo_structure:
                self.altitude = geo_structure["altitude"]

        self.line_wikidata_ids: list[int] = []

        if WIKIDATA_PROPERTY_LINE in self.claims:
            for claim in self.claims[WIKIDATA_PROPERTY_LINE]:
                if "datavalue" not in claim["mainsnak"]:
                    logging.warning("[WIKIDATA] no value for line for " + name)
                    continue
                if "qualifiers" in claim:
                    qualifiers = claim["qualifiers"]
                    if WIKIDATA_PROPERTY_END_DATE in qualifiers:
                        continue
                line_wikidata_id: int = get_value(claim)["numeric-id"]
                self.line_wikidata_ids.append(line_wikidata_id)

        self.next_connections: list[list[int, int]] = []

        if WIKIDATA_PROPERTY_NEXT_STATION in self.claims:
            for claim in self.claims[WIKIDATA_PROPERTY_NEXT_STATION]:
                if "datavalue" not in claim["mainsnak"]:
                    logging.warning("[WIKIDATA] no value for next station for " + name)
                    continue
                specified_line_wikidata_id: Optional[int] = None
                if "qualifiers" in claim:
                    qualifiers = claim["qualifiers"]
                    if WIKIDATA_PROPERTY_LINE in qualifiers:
                        for qualifier in qualifiers[WIKIDATA_PROPERTY_LINE]:
                            specified_line_wikidata_id: int = qualifier["datavalue"]["value"]["numeric-id"]
                next_station_wikidata_id: int = get_value(claim)["numeric-id"]

                # Try to assume line

                line_wikidata_id = 0
                if specified_line_wikidata_id:
                    line_wikidata_id = specified_line_wikidata_id
                if len(self.line_wikidata_ids) == 1:
                    line_wikidata_id = self.line_wikidata_ids[0]

                self.next_connections.append([next_station_wikidata_id, line_wikidata_id])

        self.transition_connections: list[int] = []

        if WIKIDATA_PROPERTY_TRANSITION_STATION in self.claims:
            for claim in self.claims[WIKIDATA_PROPERTY_TRANSITION_STATION]:
                if "datavalue" not in claim["mainsnak"]:
                    logging.warning(f"[WIKIDATA] no value for next station for {name}")
                    continue
                transition_station_wikidata_id: int = get_value(claim)["numeric-id"]
                self.transition_connections.append(transition_station_wikidata_id)

        self.height = None

        if WIKIDATA_PROPERTY_VERTICAL_DEPTH in self.claims:
            for claim in self.claims[WIKIDATA_PROPERTY_VERTICAL_DEPTH]:
                if "datavalue" not in claim["mainsnak"]:
                    logging.warning("[WIKIDATA] no value vertical depth for station")
                    continue
                if get_value(claim)["unit"].endswith(WIKIDATA_ITEM_METER):
                    self.height: float = -float(get_value(claim)["amount"])
                else:
                    logging.warning(f"unsupported unit {get_value(claim)['unit']}")

        self.stations: list[Station] = []

        # if not self.line_wikidata_ids:
        # FIXME: Line is empty for Moscow monorail stations. Have to think about more accurate fix.
        # self.line_wikidata_ids = [0]

    def fill_station(self, station: Station):
        station.set_names(self.names)
        station.geo_position = self.geo_position
        station.open_time = self.open_time
        station.site_links = self.site_links
        station.altitude = self.height
        station.status = self.status
        self.stations.append(station)

    def get_stations(self) -> list[Station]:
        return self.stations


class WikidataLineItem(WikidataItem):
    def __init__(self, structure: dict[str, Any], wikidata_id: int, local_languages: list[str] = None):
        super().__init__(structure, wikidata_id)

        self.id_ = data.compute_line_id(self.names, local_languages)

        self.color = None

        if WIKIDATA_PROPERTY_COLOR in self.claims:
            self.color = "#" + get_value(self.claims[WIKIDATA_PROPERTY_COLOR][0])

        if WIKIDATA_PROPERTY_COMPLEX_COLOR in self.claims:
            if "qualifiers" in self.claims[WIKIDATA_PROPERTY_COMPLEX_COLOR][0]:
                for qualifier in self.claims[WIKIDATA_PROPERTY_COMPLEX_COLOR][0]["qualifiers"]:
                    if qualifier == WIKIDATA_PROPERTY_COLOR:
                        self.color = (
                            "#"
                            + self.claims[WIKIDATA_PROPERTY_COMPLEX_COLOR][0]["qualifiers"][WIKIDATA_PROPERTY_COLOR][0][
                                "datavalue"
                            ]["value"]
                        )

        self.system_wikidata_id = None

        if WIKIDATA_PROPERTY_PART_OF in self.claims:
            self.system_wikidata_id = get_value(self.claims[WIKIDATA_PROPERTY_PART_OF][0])["numeric-id"]

        if WIKIDATA_PROPERTY_TRANSPORT_NETWORK in self.claims:
            self.system_wikidata_id = get_value(self.claims[WIKIDATA_PROPERTY_TRANSPORT_NETWORK][0])["numeric-id"]

    def create_line(self) -> Line:
        """Create new line object from line Wikidata item."""
        line = Line({}, self.id_)
        if self.color:  # and not line.has_color():
            line.color = self.color
        for language in self.names:
            name = data.extract_line_name(self.names[language], language)
            line.set_name(language, name)
        return line

    def fill_line(self, line: Line) -> None:
        """
        Fill existed line object with data from line Wikidata item.

        :param line: existed Wikidata object.
        """
        if self.color:  # and not line.has_color():
            line.color = self.color
        for language in self.names:
            name = data.extract_line_name(self.names[language], language)
            line.set_name(language, name)


class WikidataSystemItem(WikidataItem):
    pass


@dataclass
class WikidataParser:
    cache_directory: Path

    def parse_wikidata(self, wikidata_id: int) -> dict:
        """Parse Wikidata item by its ID."""
        parameters = {"action": "wbgetentities", "format": "json", "ids": WIKIDATA_ITEM_PREFIX + str(wikidata_id)}
        content: bytes = network.get(
            "www.wikidata.org/w/api.php",
            parameters,
            self.cache_directory / (WIKIDATA_ITEM_PREFIX + str(wikidata_id)),
        )
        return json.loads(content.decode())


class WikidataCityParser:
    def __init__(
        self,
        wikidata_parser: WikidataParser,
        map_: Map,
        systems_dict: dict[int, str],
        wikidata_init_ids: list[int],
        wikidata_id: int,
        network_update: list[str],
    ) -> None:

        self.wikidata_parser = wikidata_parser
        self.network_update = network_update
        self.wikidata_id = wikidata_id

        self.parsed_station_wikidata_ids = set()
        self.to_parse_station_wikidata_ids = set(wikidata_init_ids)

        self.parsed_line_wikidata_ids = set()
        self.to_parse_line_wikidata_ids = set()

        self.map = map_

        self.systems_dict: dict[int, System] = {}

        system_wikidata_id: int
        for system_wikidata_id in systems_dict:
            self.systems_dict[system_wikidata_id] = map_.systems[systems_dict[system_wikidata_id]]

    def parse(self, limit: Optional[int] = None) -> None:

        # TODO: add filter, so we can parse only stations of one line, or at least of one city.

        if self.wikidata_id:
            structure = self.wikidata_parser.parse_wikidata(self.wikidata_id)
            item = WikidataSystemItem(structure, self.wikidata_id)
            self.map.names = item.names

        # Preprocessing: get all Wikidata items we need.

        # Map Wikidata ids to Wikidata page descriptions.
        station_items: dict[int, WikidataStationItem] = {}
        line_items: dict[int, WikidataLineItem] = {}

        count: int = 0
        while len(self.to_parse_station_wikidata_ids) > 0:
            wikidata_id: int = self.to_parse_station_wikidata_ids.pop()

            structure: dict = self.wikidata_parser.parse_wikidata(wikidata_id)
            station_item: WikidataStationItem = WikidataStationItem(structure, wikidata_id)
            pattern: str
            for pattern in self.network_update:
                en_name = station_item.get_name("en")
                if en_name and re.match(".*" + pattern + ".*", en_name):
                    structure: dict = self.wikidata_parser.parse_wikidata(wikidata_id)
                    station_item = WikidataStationItem(structure, wikidata_id)

            self.parsed_station_wikidata_ids.add(wikidata_id)

            line_wikidata_id: int
            for line_wikidata_id in station_item.line_wikidata_ids:
                if line_wikidata_id not in self.parsed_line_wikidata_ids:
                    structure: dict = self.wikidata_parser.parse_wikidata(line_wikidata_id)
                    line_item: WikidataLineItem = WikidataLineItem(
                        structure, line_wikidata_id, self.map.local_languages
                    )
                    line_items[line_wikidata_id] = line_item
                    self.parsed_line_wikidata_ids.add(line_wikidata_id)

            count += 1
            if limit and count > limit:
                break

            line_wikidata_id: int
            for line_wikidata_id in station_item.line_wikidata_ids:
                station_item.system_wikidata_ids.add(line_items[line_wikidata_id].system_wikidata_id)

            # If this station is not the part of systems of interest, skip it.

            is_system_of_interest: bool = False

            system_wikidata_id: int
            for system_wikidata_id in station_item.system_wikidata_ids:
                if system_wikidata_id in self.systems_dict:
                    is_system_of_interest = True
                    break

            line_wikidata_id: int
            for line_wikidata_id in station_item.line_wikidata_ids:
                if line_wikidata_id in self.systems_dict:
                    is_system_of_interest = True
                    break

            if not is_system_of_interest:
                logging.info("not interested in " + station_item.get_any_name())
                continue

            station_items[wikidata_id] = station_item

            # Add station IDs to parse in the future.

            other_id: int
            for other_id in station_item.transition_connections:
                if (
                    other_id not in self.parsed_station_wikidata_ids
                    and other_id not in self.to_parse_station_wikidata_ids
                ):
                    self.to_parse_station_wikidata_ids.add(other_id)

            other_id: int
            for other_id, _ in station_item.next_connections:
                if (
                    other_id not in self.parsed_station_wikidata_ids
                    and other_id not in self.to_parse_station_wikidata_ids
                ):
                    self.to_parse_station_wikidata_ids.add(other_id)

        # Now we have all station and line Wikidata items.

        # Add lines to system or fill with data.

        lines: dict[int, Line] = {}

        line_wikidata_id: int
        line_item: WikidataLineItem
        for line_wikidata_id, line_item in line_items.items():
            system: Optional[System] = None
            line: Optional[Line] = None
            # If line's system is system of interest.
            if line_item.system_wikidata_id and line_item.system_wikidata_id in self.systems_dict:
                system = self.systems_dict[line_item.system_wikidata_id]
                line = system.lines[line_item.id_] if line_item.id_ in system.lines else None
            # If system itself was defined as a line (if there is only one line in transport system).
            elif line_wikidata_id in self.systems_dict:
                system = self.systems_dict[line_wikidata_id]
                line = system.lines[line_item.id_]
            if system:
                if line:
                    line_item.fill_line(line)
                    lines[line_wikidata_id] = line
                else:
                    line = line_item.create_line()
                    system.lines[line.id_] = line
                    lines[line_wikidata_id] = line

        # Process stations.

        stations: dict[int, list[Station]] = {}

        station_wikidata_id: int
        for station_wikidata_id in station_items:
            station_item: WikidataStationItem = station_items[station_wikidata_id]

            item_stations: list[Station] = []

            line_wikidata_id: int
            for line_wikidata_id in station_item.line_wikidata_ids:
                if line_wikidata_id not in lines:  # It is not line of interest.
                    continue
                line: Line = lines[line_wikidata_id]
                station_id = (
                    line.id_ + "/" + data.compute_short_station_id(station_item.names, self.map.local_languages)
                )
                if station_id:
                    station = Station({}, station_id)
                    station.line = line
                    station_item.fill_station(station)
                    item_stations.append(station)
                else:
                    logging.error("cannot compute station ID")

            # Connect all stations inside one Wikidata stations item.
            # TODO: check if we need ConnectionType.SAME here.

            station: Station
            for station in item_stations:
                other_station: Station
                for other_station in item_stations:
                    if station != other_station:
                        station.add_connection(other_station, ConnectionType.TRANSITION)
                        other_station.add_connection(station, ConnectionType.TRANSITION)

            stations[station_wikidata_id] = item_stations

        station_wikidata_id: int
        for station_wikidata_id in station_items:
            station_item: WikidataStationItem = station_items[station_wikidata_id]

            for other_station_wikidata_id, line_wikidata_id in station_item.next_connections:
                if other_station_wikidata_id not in station_items:
                    continue
                other_station_item: WikidataStationItem = station_items[other_station_wikidata_id]
                common_lines = set.intersection(
                    set(station_item.line_wikidata_ids), set(other_station_item.line_wikidata_ids)
                )
                station: Station
                for station in station_item.stations:
                    other_station: Station
                    for other_station in other_station_item.stations:
                        if station.line == other_station.line or not common_lines:
                            station.add_connection(other_station, ConnectionType.NEXT)

            other_station_wikidata_id: int
            for other_station_wikidata_id in station_item.transition_connections:
                if other_station_wikidata_id not in station_items:
                    continue
                other_station_item: WikidataStationItem = station_items[other_station_wikidata_id]
                station: Station
                for station in station_item.stations:
                    other_station: Station
                    for other_station in other_station_item.stations:
                        station.add_connection(other_station, ConnectionType.TRANSITION)

        # Finally add all generated stations to system.

        station_item: WikidataStationItem
        for station_item in station_items.values():
            station: Station
            for station in station_item.get_stations():
                station.recompute()
                line = station.line
                station_system = None
                system: System
                for system in self.map.systems.values():
                    if line in system.lines.values():
                        station_system = system
                if station_system:
                    station_system.stations[station.id_] = station
