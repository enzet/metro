import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from metro.core.line import Line
from metro.core.named import Named
from metro.core.station import Connection, Station

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"


DEFAULT_STYLE_ID: str = "normal"


@dataclass
class System(Named):
    """Transport system."""

    id_: str
    stations: dict[str, Station] = field(default_factory=dict)
    lines: dict[str, Line] = field(default_factory=dict)
    lookup_station_id: dict[str, Station] = field(default_factory=dict)
    style_id: Optional[str] = None
    line_width: Optional[float] = None
    point_length: Optional[float] = None

    def deserialize(self, structure: dict[str, Any]):
        """Deserialize transport system from structure."""

        if "lines" in structure:
            line: dict[str, Any]
            for line in structure["lines"]:
                self.lines[line["id"]] = Line({}, line["id"]).deserialize(line)

        if "stations" in structure:
            station_structure: dict[str, Any]
            for station_structure in structure["stations"]:
                station: Station = Station({}, station_structure["id"]).deserialize(station_structure, self.lines)
                if "line" in station_structure:
                    station.line = self.lines[station_structure["line"]]
                self.stations[station.id_] = station

            for station_structure in structure["stations"]:
                if "connections" in station_structure:
                    station: Station = self.stations[station_structure["id"]]
                    for connection_structure in station_structure["connections"]:
                        station.connections.append(Connection.deserialize(connection_structure, self.stations))

        for key in structure:
            value = structure[key]

            if key == "id":
                self.id_ = value

            elif key == "line_width":
                self.line_width = value

            elif key == "names":
                self.set_names(value)

            elif key not in ["lines", "stations"]:
                logging.warning("ignored key " + key + " for system")

    def serialize(self) -> dict[str, Any]:
        """Serialize transport system to structure."""
        return {
            "id": self.id_,
            "stations": [x.serialize() for x in self.stations.values()],
            "lines": [x.serialize() for x in self.lines.values()],
        } | ({"line_width": self.line_width} if self.line_width else {})

    def get_style_id(self) -> str:
        return self.style_id if self.style_id else DEFAULT_STYLE_ID

    # Station.

    def get_stations_by_short_id(self, station_short_id) -> list[Station]:
        result = []
        station: Station
        for station in self.stations.values():
            if (station.short_id() == station_short_id) or (
                station.id_ and station.id_.endswith("/" + station_short_id)
            ):
                result.append(station)
        return result

    def get_station_by_wikidata_id(self, station_wikidata_id) -> Optional[Station]:
        station: Station
        for station in self.stations.values():
            if station.wikidata_id == station_wikidata_id:
                return station
        return None

    def get_station_by_line_and_wid(self, line_id, station_wikidata_id) -> Optional[Station]:
        station: Station
        for station in self.stations:
            if station.wikidata_id == station_wikidata_id and station.line_id == line_id:
                return station
        return None

    def get_stations_by_name(self, name: str, language: str) -> list[Station]:
        result = []
        station: Station
        for station in self.stations:
            if station.has_name(language) and station.get_caption(language) == name:
                result.append(station)
        return result

    def get_stations_by_line(self, line: Line) -> list[Station]:
        result = []
        station: Station
        for station in self.stations:
            if station.line == line:
                result.append(station)
        return result

    # Line.

    def has_transitions(self) -> bool:
        """If there is at least one transition station."""
        return any(station.is_transition() for station in self.stations.values())

    def get_station_unique_names(self, language: str) -> set[str]:
        return {x.get_caption(language) for x in self.stations.values()}

    def get_depth_bounds(self) -> tuple[float, float]:
        if not len(self.stations):
            raise Exception()

        bounds: tuple[float, float] = (list(self.stations.values())[0].altitude,) * 2
        for station in self.stations.values():
            height: float = station.altitude
            bounds = (min(bounds[0], height), max(bounds[1], height))
        return bounds


@dataclass
class Map:
    id_: str
    names: dict[str, str] = field(default_factory=dict)
    systems: dict[str, System] = field(default_factory=dict)
    local_languages: list[str] = field(default_factory=list)

    def get_system_by_id(self, system_id: str) -> System:
        return self.systems[system_id]

    def set_names(self, names: dict[str, str]) -> None:
        self.names = names

    def get_local_languages(self) -> list[str]:
        return self.local_languages

    def get_systems(self):
        return self.systems.values()
